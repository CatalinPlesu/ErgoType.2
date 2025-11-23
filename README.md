# ErgoType - Keyboard Layout Optimization System

A modern C# implementation of genetic algorithm-based keyboard layout optimization with advanced fitness evaluation, parallel processing, and comprehensive keyboard layout analysis.

## 🚀 Quick Start

```bash
dotnet run --project ErgoType.csproj
```

## ✨ Features

### 🧬 Genetic Algorithm
- **Tournament Selection**: k-ary tournament selection with configurable tournament size
- **Uniform Crossover**: Advanced uniform crossover with bias towards better parents  
- **Mutation**: Swap-based mutation with adaptive rates based on stagnation
- **Elitism**: Survivor selection preserving the best individuals
- **Parallel Processing**: Multi-core fitness evaluation

### 🎯 Fitness Evaluation  
- **Frequency-Based**: Uses English letter/bigram frequencies and keyboard geometry
- **Text-Based**: Processes raw text files with configurable sample text
- **Simplified Fitness**: Fast distance + time calculation with normalization
- **Caching System**: Prevents redundant fitness calculations
- **Configurable Weights**: Adjustable distance vs time component weights

### 🏗️ Architecture
- **Clean Code**: Modern C# with nullable reference types, records, and pattern matching
- **Flexible Design**: Strategy pattern for fitness evaluation, factory patterns for object creation
- **Type Safety**: Strong typing throughout with validation and error handling
- **Extensible**: Easy to add new fitness functions, algorithms, and keyboard layouts

### 🚀 Performance
- **Parallel Processing**: Multi-threaded fitness evaluation
- **Memory Efficient**: Optimized data structures and algorithms  
- **Fast Evaluation**: Simplified fitness functions for rapid iteration
- **Caching**: Fitness result caching to avoid redundant calculations

## 📁 Project Structure

```
ErgoType/
├── ErgoType.Core/              # Core algorithms and data structures
├── ErgoType.UI/                # Console interface and visualization  
├── ErgoType.Data/              # Keyboard layouts and datasets
├── ErgoType.Tests/             # Unit tests and benchmarks
└── ErgoType.sln                # Visual Studio solution
```

## 🔧 Configuration

The system supports extensive configuration through `appsettings.json`:

```json
{
  "GeneticAlgorithm": {
    "PopulationSize": 50,
    "MaxGenerations": 100,
    "TournamentSize": 3,
    "MutationRate": 0.05,
    "StagnationLimit": 15
  },
  "Fitness": {
    "DistanceWeight": 0.7,
    "TimeWeight": 0.3,
    "UseSimplifiedFitness": true
  }
}
```

## 💻 Usage Examples

### Basic Optimization
```csharp
var optimizer = new KeyboardLayoutOptimizer();
var bestLayout = optimizer.Optimize(new OptimizationConfig {
    PopulationSize = 30,
    MaxGenerations = 50,
    KeyboardLayout = "ANSI_60%"
});
```

### Custom Fitness Function
```csharp
var customFitness = new CustomFitnessEvaluator(
    distanceWeight: 0.6,
    timeWeight: 0.4
);
optimizer.SetFitnessEvaluator(customFitness);
```

### Layout Comparison
```csharp
var layouts = new[] { "QWERTY", "DVORAK", "COLEMAK" };
var results = optimizer.CompareLayouts(layouts);
```

## 🎹 Keyboard Support

- **ANSI 60%**: Standard 60% keyboard layout
- **Dactyl ManuForm**: Ergonomic split keyboard  
- **Ferris Sweep**: Modern ergonomic layout
- **Custom Layouts**: JSON-based layout definition

## 📊 Fitness Components

### Distance Score
Calculates total finger travel distance based on:
- Key positions on keyboard
- Finger assignments and reach
- N-gram frequency data

### Time Score  
Estimates typing time using:
- Fitts' law for movement time
- Finger strength and dexterity weights
- Parallel finger movement simulation

### Normalization
Fitness values are normalized to 0-1 range where:
- 1.0 = Best possible layout
- 0.0 = Worst possible layout
- Values computed relative to current population bounds

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch  
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.