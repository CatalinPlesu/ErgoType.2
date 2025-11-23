# ErgoType - C# Keyboard Layout Optimization

A modern C# implementation of genetic algorithm-based keyboard layout optimization with advanced fitness evaluation, parallel processing, and comprehensive keyboard layout analysis.

## 🚀 Quick Start

```bash
# Build the solution
dotnet build ErgoType.sln

# Run the console application
dotnet run --project ErgoType.UI/ErgoType.UI.csproj

# Run tests
dotnet test ErgoType.Tests/ErgoType.Tests.csproj
```

## ✨ Features

### 🧬 Genetic Algorithm
- **Tournament Selection**: k-ary tournament selection with configurable tournament size
- **Uniform Crossover**: Advanced uniform crossover with bias towards better parents  
- **Mutation**: Swap-based mutation with adaptive rates based on stagnation
- **Elitism**: Survivor selection preserving the best individuals
- **Parallel Processing**: Multi-core fitness evaluation using `Parallel.ForEach`

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
│   ├── KeyboardLayout.cs       # Layout representation
│   ├── Individual.cs           # GA individual
│   ├── Key.cs                  # Key definition
│   ├── Finger.cs               # Finger enum and extensions
│   ├── Keyboard.cs             # Keyboard layout
│   ├── GeneticAlgorithm/       # GA implementation
│   ├── Fitness/                # Fitness evaluation
│   └── KeyboardLayoutOptimizer.cs
├── ErgoType.UI/                # Console interface and visualization  
│   └── Program.cs              # Main application
├── ErgoType.Data/              # Keyboard layouts and datasets
│   └── KeyboardFactory.cs      # Keyboard creation
└── ErgoType.Tests/             # Unit tests and benchmarks
    └── KeyboardLayoutTests.cs  # Test suite
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
var customFitness = new SimplifiedFitnessEvaluator(new FitnessConfig {
    DistanceWeight = 0.6,
    TimeWeight = 0.4
});
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

## 🎮 Console Interface

The application provides a beautiful console interface using Spectre.Console:

```
What would you like to do?

➤ Optimize - Run genetic algorithm optimization
  Compare - Compare existing keyboard layouts  
  Evaluate - Evaluate a single layout
  Demo - Run demonstration
  Exit - Quit the application
```

### Demo Mode
Run `dotnet run --project ErgoType.UI -- --demo` to see a complete demonstration:
- Comparison of existing layouts (QWERTY, Dvorak, Colemak, Workman)
- Genetic algorithm optimization with progress tracking
- Results display with fitness scores and timing

## 🧪 Testing

The project includes comprehensive unit tests:

```bash
# Run all tests
dotnet test

# Run specific test
dotnet test --filter "CanCreateKeyboard"
```

## 🎯 Algorithm Details

### Genetic Algorithm Process
1. **Initialization**: Create population with heuristic and random layouts
2. **Evaluation**: Calculate fitness for all individuals (parallel)
3. **Selection**: Tournament selection to choose parents
4. **Crossover**: Uniform crossover with bias towards better parents
5. **Mutation**: Swap mutation with adaptive rates
6. **Replacement**: Elitist survivor selection
7. **Termination**: Stop after max generations or stagnation limit

### Fitness Calculation
1. **Distance**: Sum of finger travel distances for common text
2. **Time**: Fitts' law-based movement time with finger strength
3. **Normalization**: Scale to 0-1 range based on population bounds
4. **Combined**: Weighted sum with distance and time components

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch  
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.