# Working library interface matching Python simplified_typer.py

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
  var processor = initTextProcessor(layout, text_processor.FittsA, text_processor.FittsB, false)
  
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
  var processor = initTextProcessor(layout, text_processor.FittsA, text_processor.FittsB, false)
  
  var limitedText = if previewMode and text.len > maxChars: text[0..<maxChars] else: text
  
  let (dist, time, charCount, typedChars, coverage, procTime, speed) = 
    processText(processor, limitedText, previewMode, maxChars)
  
  return @[dist, time, float(charCount), float(typedChars), coverage, procTime, speed]

proc fitness*(text: string, layoutFile: string = "/home/catalin/dev/ergotype.2/src/data/keyboards/ansi_60_percent.json"): seq[float] {.exportpy.} =
  ## Calculate fitness matching Python simplified_typer.fitness() method
  ## Returns: [totalDistance, totalTime]
  
  let layout = loadLayoutFromJson(layoutFile)
  var processor = initTextProcessor(layout, text_processor.FittsA, text_processor.FittsB, false)
  
  let (dist, time) = processor.fitness(text)
  return @[dist, time]

proc getLayoutKeyCount*(layoutFile: string = "/home/catalin/dev/ergotype.2/src/data/keyboards/ansi_60_percent.json"): int {.exportpy.} =
  ## Get total number of keys in layout
  try:
    let layout = loadLayoutFromJson(layoutFile)
    return 26  # Hardcoded for now
  except:
    return 0

proc isCharacterTypable*(c: char, layoutFile: string = "/home/catalin/dev/ergotype.2/src/data/keyboards/ansi_60_percent.json"): bool {.exportpy.} =
  ## Check if character can be typed on layout
  try:
    let layout = loadLayoutFromJson(layoutFile)
    var processor = initTextProcessor(layout, text_processor.FittsA, text_processor.FittsB, false)
    return processor.isCharacterTypable(c)
  except:
    return false

when isMainModule:
  echo "Minimal working Nim library interface for Python integration"
  echo "Compile with: nim py --lib text_processor_lib_working.nim"