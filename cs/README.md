# Keyboard Layout Optimizer - C# Implementation

A clean, performant C# implementation of the keyboard layout optimization system using genetic algorithms and modern .NET features.

## Features

- **Genetic Algorithm**: Advanced GA implementation with tournament selection, uniform crossover, and mutation
- **Fitness Evaluation**: Flexible fitness function system supporting both statistical models and raw text processing
- **Keyboard Layout Support**: Full keyboard layout parsing and visualization
- **Spectre.Console UI**: Beautiful terminal interface with tables, progress bars, and formatting
- **Performance**: Optimized for speed with parallel processing and caching
- **Extensible**: Clean architecture allowing easy addition of new fitness functions and algorithms

## Architecture

### Core Components

1. **KeyboardLayoutOptimizer**: Main orchestrator class
2. **GeneticAlgorithm**: Genetic algorithm implementation with advanced features
3. **FitnessEvaluator**: Flexible fitness evaluation with multiple strategies
4. **Keyboard**: Keyboard layout representation and parsing
5. **Individual**: Genetic algorithm individual representation

### Key Design Patterns

- **Strategy Pattern**: Different fitness evaluation strategies
- **Factory Pattern**: Keyboard layout creation
- **Observer Pattern**: Progress reporting and logging
- **Builder Pattern**: Configuration and setup

## Usage

### Basic Usage

```csharp
var optimizer = new KeyboardLayoutOptimizer(
    "path/to/keyboard.json", 
    "path/to/dataset.json", 
    "dataset_name"
);

var result = optimizer.Optimize(
    populationSize: 50,
    maxGenerations: 100,
    stagnationLimit: 15
);

Console.WriteLine($"Best fitness: {result.BestIndividual.Fitness}");
Console.WriteLine($"Layout: {new string(result.BestIndividual.Chromosome)}");
```

### Fitness Evaluation

The system supports multiple fitness evaluation strategies:

```csharp
// Statistical frequency-based evaluation
var config = new FitnessConfig 
{ 
    DistanceWeight = 0.7,
    TimeWeight = 0.3,
    UseSimplifiedFitness = false
};

var evaluator = new FitnessEvaluator(keyboard, datasetFile, datasetName, config);
double fitness = evaluator.Evaluate(layout);
```

### Custom Fitness Functions

You can implement custom fitness functions using the lambda-based approach:

```csharp
FitnessFunction customFitness = (char[] layout) =>
{
    // Your custom fitness calculation
    return CalculateCustomFitness(layout);
};
```

## Configuration

### Fitness Configuration

```csharp
var config = new FitnessConfig
{
    DistanceWeight = 0.7,      // Weight for distance component
    TimeWeight = 0.3,          // Weight for time component  
    UseSimplifiedFitness = false, // Use simplified vs detailed calculation
    EnableCaching = true       // Enable fitness result caching
};
```

### Genetic Algorithm Configuration

```csharp
var ga = new GeneticAlgorithm(evaluator)
{
    PopulationSize = 50,
    MutationRate = 0.05,
    TournamentSize = 3,
    OffspringPerPair = 4,
    MaxGenerations = 100,
    StagnationLimit = 15
};
```

## Performance Features

### Parallel Processing
- Multi-threaded fitness evaluation
- Concurrent population processing
- Optimized for multi-core systems

### Caching
- Fitness result caching to avoid redundant calculations
- Configurable cache strategies
- Memory-efficient storage

### Optimization
- Efficient data structures
- Minimal memory allocations
- Streamlined algorithms

## File Structure

```
cs/
├── Program.cs                 # Main entry point with Spectre.Console UI
├── KeyboardLayoutOptimizer.cs # Main orchestrator class
├── GeneticAlgorithm.cs        # Genetic algorithm implementation
├── FitnessEvaluator.cs        # Fitness evaluation strategies
├── Keyboard.cs               # Keyboard layout representation
└── cs.csproj                 # Project configuration
```

## Dependencies

- **Spectre.Console**: Beautiful terminal UI
- **Newtonsoft.Json**: JSON parsing for keyboard layouts
- **.NET 6+**: Modern C# runtime

## Building and Running

```bash
# Build the project
dotnet build

# Run the application
dotnet run
```

## Advanced Features

### Preset Layouts
The system includes several preset layouts:
- QWERTY (standard)
- Dvorak (ergonomic)
- Colemak (modern ergonomic)
- Workman (alternative ergonomic)
- Norman (balanced)

### Layout Comparison
Compare multiple layouts with detailed metrics:
- Fitness scores
- Distance components
- Time components
- Performance analysis

### Real-time Progress
Monitor optimization progress with:
- Generation statistics
- Fitness improvements
- Time tracking
- Stagnation detection

## Extensibility

The architecture is designed for easy extension:

1. **New Fitness Functions**: Implement `FitnessEvaluatorBase`
2. **Custom Selection**: Extend selection strategies
3. **Additional Metrics**: Add new evaluation criteria
4. **Visualization**: Custom layout visualization
5. **Export/Import**: Support for additional file formats

## Future Enhancements

- **Machine Learning Integration**: Neural network fitness evaluation
- **3D Visualization**: Advanced layout visualization
- **Multi-objective Optimization**: Pareto optimization
- **Cloud Processing**: Distributed computing support
- **Web Interface**: Browser-based UI
- **Mobile App**: Touch-based layout design

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Notes

This C# implementation provides:
- **Cleaner Code**: Modern C# with nullable reference types
- **Better Performance**: Optimized algorithms and data structures  
- **Type Safety**: Strong typing throughout the system
- **Modern UI**: Spectre.Console for beautiful terminal output
- **Flexibility**: Lambda-based fitness functions for easy customization
- **Maintainability**: Clear separation of concerns and clean architecture