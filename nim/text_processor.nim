# Minimal Nim port of simplified typer for keyboard layout fitness calculation

import strutils
import math
import times
import sequtils
import json
import tables
import os

# Minimal data structures matching Python simplified_typer.py
type
  KeyData* = object
    id*: int
    char*: char
    finger*: int
    x*: float
    y*: float
    hand*: int  # 0 = left, 1 = right

  FingerState* = object
    fingerId*: int
    homingKeyId*: int
    currentKeyId*: int
    totalDistance*: float
    totalTime*: float
    keyCount*: int
    activeInWindow*: bool

  MinimalLayout* = object
    keyMap*: Table[char, KeyData]
    reverseMap*: Table[int, KeyData]
    fingerMap*: Table[int, KeyData]  # Map key ID to KeyData

  FittsCalculator* = object
    fittsA*: float
    fittsB*: float
    fingerTimeBase*: Table[int, float]  # Finger-specific time factors

  ModifierKeys* = object
    shiftKeys*: seq[int]  # Key IDs for shift keys
    altgrKeys*: seq[int]  # Key IDs for AltGr keys

# Constants matching Python version
const FingerNames* = ["PINKY_LEFT", "RING_LEFT", "MIDDLE_LEFT", "INDEX_LEFT", "INDEX_RIGHT", "MIDDLE_RIGHT", "RING_RIGHT", "PINKY_RIGHT"]
const FingerValues* = [0, 1, 2, 3, 4, 5, 6, 7]
const HandNames* = ["LEFT", "RIGHT"]
const HandValues* = [0, 1]

# Config-like constants (can be adjusted)
const SimulationWindowSize* = 256
const ParallelTypingEnabled* = true
const SynchronousEnd* = true
const FittsA* = 0.0
const FittsB* = 150.0

# Finger time factors
var FingerTimeBase*: Table[int, float] = initTable[int, float]()
proc initFingerTimeBase() =
  FingerTimeBase[0] = 1.2  # PINKY_LEFT
  FingerTimeBase[1] = 1.1  # RING_LEFT  
  FingerTimeBase[2] = 1.05 # MIDDLE_LEFT
  FingerTimeBase[3] = 1.0  # INDEX_LEFT
  FingerTimeBase[4] = 1.0  # INDEX_RIGHT
  FingerTimeBase[5] = 1.05 # MIDDLE_RIGHT
  FingerTimeBase[6] = 1.1  # RING_RIGHT
  FingerTimeBase[7] = 1.2  # PINKY_RIGHT

# Initialize the table
initFingerTimeBase()

proc initKeyData*(id: int, c: char, finger: int, x, y: float, hand: int = 0): KeyData =
  KeyData(id: id, char: c, finger: finger, x: x, y: y, hand: hand)

proc distanceTo*(a: KeyData, b: KeyData): float =
  sqrt((a.x - b.x)^2 + (a.y - b.y)^2)

proc initFingerState*(fingerId, homingKeyId: int): FingerState =
  result = FingerState(
    fingerId: fingerId,
    homingKeyId: homingKeyId,
    currentKeyId: homingKeyId,
    totalDistance: 0.0,
    totalTime: 0.0,
    keyCount: 0,
    activeInWindow: false
  )

proc initFittsCalculator*(fittsA, fittsB: float): FittsCalculator =
  var fingerFactors: Table[int, float] = initTable[int, float]()
  for key, value in FingerTimeBase.pairs:
    fingerFactors[key] = value
  
  FittsCalculator(fittsA: fittsA, fittsB: fittsB, fingerTimeBase: fingerFactors)

proc initModifierKeys*(): ModifierKeys =
  ModifierKeys(shiftKeys: @[], altgrKeys: @[])

proc calculateFittsTime*(calc: FittsCalculator, distance: float, fingerId: int): float =
  if distance <= 0.0: 
    return 0.01  # Small fallback time
  
  let baseTime = calc.fittsA + calc.fittsB * log2(distance + 1.0)
  let fingerFactor = calc.fingerTimeBase.getOrDefault(fingerId, 1.0)
  result = baseTime * fingerFactor

proc loadLayoutFromJson*(filename: string): MinimalLayout =
  if not fileExists(filename):
    raise newException(ValueError, "Layout file not found: " & filename)
  
  let content = readFile(filename)
  let jsonData = parseJson(content)
  
  var keyMap: Table[char, KeyData]
  var reverseMap: Table[int, KeyData]
  var fingerMap: Table[int, KeyData]
  var keyId = 0
  
  # ANSI 60% layout is a 2D array of rows
  if jsonData.kind != JArray:
    raise newException(ValueError, "Expected JSON array")
  
  let rows = jsonData
  
  for rowIndex in 0..<rows.len.int:
    let row = rows[rowIndex]
    var colIdx = 0
    var i = 0
    
    while i < row.len.int:
      let item = row[i]
      
      if item.kind == JObject:
        let fingerInfo = item
        inc i
        
        if i < row.len.int:
          let label = row[i]
          if label.kind == JString:
            let labelStr = label.getStr()
            
            # Extract printable character
            for line in labelStr.split('\n'):
              let cleanLine = line.strip()
              if cleanLine.len == 1 and cleanLine[0] >= ' ' and cleanLine[0] <= '~':
                let c = cleanLine[0]
                
                # Get finger info
                let fingerName = fingerInfo["finger"].getStr()
                var finger = 0
                var hand = 0
                
                case fingerName
                of "PINKY_LEFT": finger = 0; hand = 0
                of "RING_LEFT": finger = 1; hand = 0  
                of "MIDDLE_LEFT": finger = 2; hand = 0
                of "INDEX_LEFT": finger = 3; hand = 0
                of "INDEX_RIGHT": finger = 4; hand = 1
                of "MIDDLE_RIGHT": finger = 5; hand = 1
                of "RING_RIGHT": finger = 6; hand = 1
                of "PINKY_RIGHT": finger = 7; hand = 1
                else: 
                  finger = 0; hand = 0
                
                # Grid-based positioning
                let x = float(colIdx * 19)  # Standard key spacing
                let y = float(rowIndex) * 19.0
                
                let keyData = initKeyData(keyId, c, finger, x, y, hand)
                keyMap[c] = keyData
                reverseMap[keyId] = keyData
                fingerMap[keyId] = keyData
                inc keyId
                
                break
            
            # Handle key width
            if fingerInfo.hasKey("w"):
              let width = fingerInfo["w"].getInt()
              colIdx += width
            else:
              inc colIdx
      inc i
  
  result = MinimalLayout(keyMap: keyMap, reverseMap: reverseMap, fingerMap: fingerMap)

type
  TextProcessor* = object
    layout*: MinimalLayout
    fittsCalc*: FittsCalculator
    fingerStates*: seq[FingerState]
    modifierKeys*: ModifierKeys
    debug*: bool
    
proc initTextProcessor*(layout: MinimalLayout, fittsA, fittsB: float, debug: bool = false): TextProcessor =
  var fingerStates: seq[FingerState]
  
  # Setup finger states for 8 fingers
  var homingKeys: array[8, int]
  
  # Initialize with invalid keys
  for i in 0..7:
    homingKeys[i] = -1
  
  # Find homing keys (simplified QWERTY layout)
  for keyData in layout.keyMap.values:
    case keyData.char
    of 'a':
      if keyData.finger == 0: homingKeys[0] = keyData.id  # PINKY_LEFT
      elif keyData.finger == 1: homingKeys[1] = keyData.id  # RING_LEFT
    of 's':
      if keyData.finger == 2: homingKeys[2] = keyData.id  # MIDDLE_LEFT
    of 'd':
      if keyData.finger == 3: homingKeys[3] = keyData.id  # INDEX_LEFT
    of 'f':
      if keyData.finger == 3: homingKeys[3] = keyData.id  # INDEX_LEFT
    of 'j':
      if keyData.finger == 4: homingKeys[4] = keyData.id  # INDEX_RIGHT
    of 'k':
      if keyData.finger == 5: homingKeys[5] = keyData.id  # MIDDLE_RIGHT
    of 'l':
      if keyData.finger == 6: homingKeys[6] = keyData.id  # RING_RIGHT
    of ';':
      if keyData.finger == 7: homingKeys[7] = keyData.id  # PINKY_RIGHT
    else: discard
  
  for i in 0..7:
    if homingKeys[i] != -1:
      fingerStates.add(initFingerState(i, homingKeys[i]))
  
  result = TextProcessor(
    layout: layout,
    fittsCalc: initFittsCalculator(fittsA, fittsB),
    fingerStates: fingerStates,
    modifierKeys: initModifierKeys(),
    debug: debug
  )

proc resetFingerPositions*(processor: var TextProcessor) =
  for i in 0..<processor.fingerStates.len:
    var state = processor.fingerStates[i]
    state.currentKeyId = state.homingKeyId
    state.totalDistance = 0.0
    state.totalTime = 0.0
    state.keyCount = 0
    state.activeInWindow = false
    processor.fingerStates[i] = state

proc getFingerForKey*(processor: TextProcessor, keyId: int): int =
  ## Get the finger ID for a key based on layout
  if processor.layout.fingerMap.hasKey(keyId):
    return processor.layout.fingerMap[keyId].finger
  
  # Fallback: search through all keys
  for keyData in processor.layout.keyMap.values:
    if keyData.id == keyId:
      return keyData.finger
  
  return 3  # Default to left index finger

proc isCharacterTypable*(processor: TextProcessor, c: char): bool =
  ## Check if character can be typed on this keyboard layout
  return processor.layout.keyMap.hasKey(c)

proc moveFingerInWindow*(processor: var TextProcessor, fingerId: int, keyTo: int, c: char): tuple[distance: float, time: float] =
  ## Move finger within simulation window with state persistence
  let keyFrom = processor.fingerStates[fingerId].currentKeyId
  
  # Get key positions
  if not processor.layout.reverseMap.hasKey(keyFrom) or not processor.layout.reverseMap.hasKey(keyTo):
    return (0.0, 0.01)  # Small fallback values
  
  let keyFromObj = processor.layout.reverseMap[keyFrom]
  let keyToObj = processor.layout.reverseMap[keyTo]
  
  # Calculate Euclidean distance
  let dx = keyToObj.x - keyFromObj.x
  let dy = keyToObj.y - keyFromObj.y
  var distance = sqrt(dx*dx + dy*dy)
  
  # Handle invalid distance
  if distance <= 0.0:
    if keyFrom != keyTo:
      if processor.debug:
        echo "Warning: Invalid distance calculated for different keys"
        echo "  From: (" & $keyFromObj.x & ", " & $keyFromObj.y & ") to (" & $keyToObj.x & ", " & $keyToObj.y & ")"
        echo "  Char: " & $c & ", Key from: " & $keyFrom & ", Key to: " & $keyTo
      distance = 0.1
    else:
      distance = 0.01  # Very small distance for same key
  
  # Calculate time using Fitts' Law
  var movementTime = processor.fittsCalc.calculateFittsTime(distance, fingerId)
  
  # Handle invalid time
  if movementTime <= 0.0 or movementTime > 1e10 or movementTime != movementTime:  # Check for very large values or NaN
    if processor.debug:
      echo "Warning: Invalid time calculated: " & $movementTime
      echo "  Distance: " & $distance & ", Finger: " & $fingerId
    movementTime = 0.001  # Fallback to small positive time
  
  # Update finger statistics
  var state = processor.fingerStates[fingerId]
  state.totalDistance += distance
  state.totalTime += movementTime
  inc state.keyCount
  state.currentKeyId = keyTo
  state.activeInWindow = true
  processor.fingerStates[fingerId] = state
  
  return (distance, movementTime)

proc typeCharacterSequential*(processor: var TextProcessor, c: char): tuple[distance: float, time: float] =
  ## Type a single character sequentially with modifier support
  if not processor.layout.keyMap.hasKey(c):
    return (0.0, 0.0)
  
  let keyData = processor.layout.keyMap[c]
  let keyId = keyData.id
  let fingerId = processor.getFingerForKey(keyId)
  
  var totalDistance = 0.0
  var totalTime = 0.0
  
  # Handle modifier keys (simplified)
  # For now, just type the character directly
  let (charDist, charTime) = processor.moveFingerInWindow(fingerId, keyId, c)
  totalDistance += charDist
  totalTime += charTime
  
  return (totalDistance, totalTime)

proc processParallelTyping*(processor: var TextProcessor, charSequence: string): tuple[distance: float, time: float] =
  ## Process typing with parallel finger movements and synchronous endings
  if not ParallelTypingEnabled:
    # Sequential typing
    var totalDistance = 0.0
    var totalTime = 0.0
    
    for c in charSequence:
      let (dist, time) = processor.typeCharacterSequential(c)
      totalDistance += dist
      totalTime += time
      
    return (totalDistance, totalTime)
  
  # Parallel typing simulation (simplified)
  var parallelMovements: seq[tuple[char: char, distance: float, time: float, startTime: float]] = @[]
  var currentTime = 0.0
  
  for c in charSequence:
    let (distance, time) = processor.typeCharacterSequential(c)
    parallelMovements.add((c, distance, time, currentTime))
    currentTime += 0.01  # Small offset to simulate slight asynchronicity
  
  # Calculate total time with synchronous endings
  var totalTime = 0.0
  if SynchronousEnd and parallelMovements.len > 0:
    var maxCompletionTime = 0.0
    for movement in parallelMovements:
      let completionTime = movement.startTime + movement.time
      if completionTime > maxCompletionTime:
        maxCompletionTime = completionTime
    totalTime = maxCompletionTime
  else:
    for movement in parallelMovements:
      totalTime += movement.time
  
  var totalDistance = 0.0
  for movement in parallelMovements:
    totalDistance += movement.distance
  
  return (totalDistance, totalTime)

proc processText*(processor: var TextProcessor, text: string, 
                 previewMode: bool = false, maxChars: int = 100000): tuple[
  totalDistance: float,
  totalTime: float,
  charCount: int,
  typedChars: int,
  coverage: float,
  processingTime: float,
  charsPerSecond: float
] =
  let startTime = cpuTime()
  
  var workText = text
  if previewMode and text.len > maxChars:
    workText = text[0..<maxChars]
  
  processor.resetFingerPositions()
  
  var totalDistance = 0.0
  var totalTime = 0.0
  var charCount = 0
  var typedChars = 0
  
  for c in workText:
    inc charCount
    
    # Skip non-printable characters (but allow space and basic punctuation)
    if c < ' ' and c != '\t' and c != '\n' and c != '\r':
      continue
    
    if not processor.isCharacterTypable(c):
      continue
      
    let (distance, timeMs) = processor.processParallelTyping($c)
    totalDistance += distance
    totalTime += timeMs
    inc typedChars
    
    # Reset positions occasionally to simulate breaks (every 256 chars)
    if typedChars mod SimulationWindowSize == 0:
      processor.resetFingerPositions()
  
  let processingTime = cpuTime() - startTime
  let coverage = if charCount > 0: float(typedChars) / float(charCount) * 100.0 else: 0.0
  let charsPerSecond = if processingTime > 0.0: float(typedChars) / processingTime else: 0.0
  
  return (totalDistance, totalTime, charCount, typedChars, coverage, processingTime, charsPerSecond)

proc printFingerStatistics*(processor: TextProcessor) =
  ## Print finger usage statistics for even distribution analysis
  echo "\n=== Finger Usage Statistics ==="
  
  var totalDistance = 0.0
  var totalTime = 0.0
  var totalPresses = 0
  
  for state in processor.fingerStates:
    totalDistance += state.totalDistance
    totalTime += state.totalTime
    totalPresses += state.keyCount
  
  echo "Finger          Presses    % Presses  Distance   % Distance Time       % Time    "
  echo "--------------------------------------------------------------------------------"
  
  if totalPresses > 0:
    for state in processor.fingerStates:
      let fingerName = case state.fingerId
        of 0: "PINKY_LEFT  "
        of 1: "RING_LEFT   "
        of 2: "MIDDLE_LEFT "
        of 3: "INDEX_LEFT  "
        of 4: "INDEX_RIGHT "
        of 5: "MIDDLE_RIGHT"
        of 6: "RING_RIGHT  "
        of 7: "PINKY_RIGHT "
        else: "FINGER_" & $state.fingerId & "  "
      
      let presses = state.keyCount
      let pressPct = float(presses) / float(totalPresses) * 100.0
      let distancePct = if totalDistance > 0.0: state.totalDistance / totalDistance * 100.0 else: 0.0
      let timePct = if totalTime > 0.0: state.totalTime / totalTime * 100.0 else: 0.0
      
      echo fingerName & " " & $presses & " " & formatFloat(pressPct, ffDecimal, 1) & " " & 
           formatFloat(state.totalDistance, ffDecimal, 2) & " " & 
           formatFloat(distancePct, ffDecimal, 1) & " " & 
           formatFloat(state.totalTime, ffDecimal, 2) & " " & 
           formatFloat(timePct, ffDecimal, 1)
  
  echo "--------------------------------------------------------------------------------"
  echo "TOTAL           " & $totalPresses & "     100.0     " & 
       formatFloat(totalDistance, ffDecimal, 2) & "    100.0     " & 
       formatFloat(totalTime, ffDecimal, 2) & "    100.0"

proc fitness*(processor: var TextProcessor, text: string, previewMode: bool = false, maxChars: int = 100000): tuple[distance: float, time: float] =
  ## Calculate simplified fitness matching Python simplified_typer.py
  let startTime = cpuTime()
  
  processor.resetFingerPositions()
  
  var totalDistance = 0.0
  var totalTime = 0.0
  var charCount = 0
  var typedChars = 0
  
  # Process text character by character for actual finger movement simulation
  for c in text:
    inc charCount
    
    if not processor.isCharacterTypable(c):
      continue
      
    let (distance, timeComponent) = processor.processParallelTyping($c)
    totalDistance += distance
    totalTime += timeComponent
    inc typedChars
    
    # Reset position occasionally to simulate breaks (every 256 chars)
    if typedChars mod SimulationWindowSize == 0:
      processor.resetFingerPositions()
  
  let calculationTime = cpuTime() - startTime
  
  # Debug info
  if processor.debug:
    echo "Preview fitness calculation:"
    echo "Characters processed: " & $charCount
    echo "Calculation time: " & formatFloat(calculationTime, ffDecimal, 3) & "s"
  
  # Print finger usage statistics
  processor.printFingerStatistics()
  
  # Validate results
  if totalDistance <= 0.0 or totalTime <= 0.0:
    if processor.debug:
      echo "Warning: Invalid distance (" & $totalDistance & ") or time (" & $totalTime & ") values"
      echo "Using fallback values."
    totalDistance = max(totalDistance, 0.1)  # Ensure positive
    totalTime = max(totalTime, 0.1)          # Ensure positive
  
  if processor.debug:
    echo "Fitness calculation completed:"
    echo "Characters processed: " & $charCount
    echo "Total distance: " & formatFloat(totalDistance, ffDecimal, 4)
    echo "Total time: " & formatFloat(totalTime, ffDecimal, 4)
    echo "Calculation time: " & formatFloat(calculationTime, ffDecimal, 3) & "s"
  
  return (totalDistance, totalTime)

when isMainModule:
  import strformat
  
  echo "Nim Text Processor for Keyboard Layout Fitness (Updated)"
  echo "======================================================="
  
  let layoutFile = "/home/catalin/dev/ergotype.2/src/data/keyboards/ansi_60_percent.json"
  echo "Loading layout from " & layoutFile
  
  if not fileExists(layoutFile):
    echo "Error: Layout file not found at " & layoutFile
    quit(1)
  
  let layout = loadLayoutFromJson(layoutFile)
  echo "Loaded layout with " & $layout.keyMap.len & " character mappings"
  
  # Show some mappings
  echo "\nCharacter mappings:"
  var count = 0
  for c, key in layout.keyMap:
    if count >= 10: break
    var handName: string
    if key.hand == 0:
      handName = "LEFT"
    else:
      handName = "RIGHT"
    echo "'" & $c & "' -> key " & $key.id & ", finger " & $key.finger & " (" & handName & "), pos (" & 
         formatFloat(key.x, ffDecimal, 1) & ", " & formatFloat(key.y, ffDecimal, 1) & ")"
    inc count
  
  let processor = initTextProcessor(layout, FittsA, FittsB, true)
  
  # Test with sample text
  var sampleText = "the quick brown fox jumps over the lazy dog"
  echo "\nProcessing sample text: '" & sampleText & "'"
  
  var myProcessor = processor
  let (dist, time, charCount, typedChars, coverage, procTime, speed) = 
    processText(myProcessor, sampleText)
  
  echo "\nResults:"
  echo "Characters processed: " & $charCount
  echo "Characters typed: " & $typedChars
  echo "Coverage: " & formatFloat(coverage, ffDecimal, 2) & "%"
  echo "Total distance: " & formatFloat(dist, ffDecimal, 1) & " mm"
  echo "Total time: " & formatFloat(time, ffDecimal, 1) & " ms"
  echo "Processing time: " & formatFloat(procTime, ffDecimal, 3) & " s"
  echo "Speed: " & formatFloat(speed, ffDecimal, 1) & " chars/sec"
  
  # Test fitness function
  echo "\nTesting fitness function:"
  let (fitnessDist, fitnessTime) = myProcessor.fitness(sampleText)
  echo "Fitness distance: " & formatFloat(fitnessDist, ffDecimal, 4)
  echo "Fitness time: " & formatFloat(fitnessTime, ffDecimal, 4)