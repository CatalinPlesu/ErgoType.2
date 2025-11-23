# Nim Library Interface for Python Integration

import nimpy
import os

# Import the main text processing functions
import text_processor

# Export functions for Python use
proc processTextFile*(filename: string, layoutFile: string = "/home/catalin/dev/ergotype.2/src/data/keyboards/ansi_60_percent.json", 
                     previewMode: bool = false, maxChars: int = 100000): seq[float] {.exportpy.} =
  ## Process a text file and return statistics as array
  ## Returns: [totalDistance, totalTime, charCount, typedChars, coverage, processingTime, charsPerSecond]
  
  let layout = loadLayoutFromJson(layoutFile)
  var processor = initTextProcessor(layout, 0.0, 150.0)
  
  # Read file
  if not fileExists(filename):
    return @[-1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0]
  
  let text = readFile(filename)
  var limitedText = if previewMode and text.len > maxChars: text[0..<maxChars] else: text
  
  let (dist, time, charCount, typedChars, coverage, procTime, speed) = 
    processText(processor, limitedText, previewMode, maxChars)
  
  return @[dist, time, float(charCount), float(typedChars), coverage, procTime, speed]

proc processTextString*(text: string, layoutFile: string = "/home/catalin/dev/ergotype.2/src/data/keyboards/ansi_60_percent.json", 
                      previewMode: bool = false, maxChars: int = 100000): seq[float] {.exportpy.} =
  ## Process text string and return statistics as array
  ## Returns: [totalDistance, totalTime, charCount, typedChars, coverage, processingTime, charsPerSecond]
  
  let layout = loadLayoutFromJson(layoutFile)
  var processor = initTextProcessor(layout, 0.0, 150.0)
  
  var limitedText = if previewMode and text.len > maxChars: text[0..<maxChars] else: text
  
  let (dist, time, charCount, typedChars, coverage, procTime, speed) = 
    processText(processor, limitedText, previewMode, maxChars)
  
  return @[dist, time, float(charCount), float(typedChars), coverage, procTime, speed]

proc getLayoutStats*(layoutFile: string = "src/data/keyboards/ansi_60_percent.json"): seq[string] {.exportpy.} =
  ## Get layout statistics
  ## Returns: [keyCount, finger0Count, finger1Count, finger2Count, finger3Count, finger4Count]
  
  let layout = loadLayoutFromJson(layoutFile)
  
  var fingerCounts: array[5, int]
  for keyData in layout.keyMap:
    if keyData.finger < 5:
      inc fingerCounts[keyData.finger]
  
  return @[
    $layout.keyMap.len,
    $fingerCounts[0],
    $fingerCounts[1], 
    $fingerCounts[2],
    $fingerCounts[3],
    $fingerCounts[4]
  ]

when is mainModule:
  echo "Nim library interface for Python integration"
  echo "Compile with: nim py --lib text_processor_lib.nim"