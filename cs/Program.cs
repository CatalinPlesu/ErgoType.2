using System;
using Spectre.Console;

namespace KeyboardLayoutOptimizer
{
    /// <summary>
    /// Main program with Spectre.Console UI
    /// </summary>
    public class Program
    {
        public static void Main(string[] args)
        {
            ShowHeader();
            
            // Run demo mode with actual genetic algorithm
            AnsiConsole.MarkupLine("[bold yellow]Running genetic algorithm optimization...[/]");
            RunOptimizationDemo();
        }

        private static void ShowHeader()
        {
            Console.Clear();
            AnsiConsole.Write(new FigletText("Keyboard Layout Optimizer")
                .Color(Color.Cyan));
            AnsiConsole.Write(new Rule());
            AnsiConsole.MarkupLine("\n[bold]Welcome to the Keyboard Layout Optimization System![/]\n");
        }

        private static void RunOptimizationDemo()
        {
            try
            {
                // Create fitness evaluator
                var config = new FitnessConfig
                {
                    DistanceWeight = 0.7,
                    TimeWeight = 0.3,
                    EnableCaching = true
                };

                var evaluator = new FrequencyBasedEvaluator(config);
                var fitnessEvaluator = new FitnessEvaluator(evaluator);
                
                // Create optimizer
                var optimizer = new KeyboardLayoutOptimizer(evaluator);
                
                AnsiConsole.MarkupLine("\n[bold yellow]Starting optimization...[/]\n");
                
                // Run optimization with smaller parameters for demo
                var result = optimizer.Optimize(
                    populationSize: 20,
                    maxGenerations: 15,
                    stagnationLimit: 5
                );

                // Show results
                AnsiConsole.MarkupLine("\n[bold green]Optimization Results:[/]\n");
                
                var table = new Table();
                table.AddColumn("Metric");
                table.AddColumn("Value");
                
                table.AddRow("Best Fitness", result.BestIndividual?.Fitness?.ToString("F6") ?? "N/A");
                table.AddRow("Elapsed Generations", result.ElapsedGenerations.ToString());
                table.AddRow("Total Time", result.TotalTime.ToString(@"hh\:mm\:ss"));
                table.AddRow("Layout", new string(result.BestIndividual?.Chromosome ?? "N/A".ToCharArray()));
                
                AnsiConsole.Write(table);

                // Show layout comparison
                AnsiConsole.MarkupLine("\n[bold blue]Layout Comparison:[/]\n");
                
                var comparisons = optimizer.CompareLayouts(
                    ("QWERTY", "abcdefghijklmnopqrstuvwxyz".ToCharArray()),
                    ("Dvorak", "aoeuidhtnsrmlqpczwbjfgkxvy".ToCharArray()),
                    ("Colemak", "qwfpgjluysemrohinctadbvkxz".ToCharArray()),
                    ("Best Found", result.BestIndividual?.Chromosome ?? "N/A".ToCharArray())
                );

                var comparisonTable = new Table();
                comparisonTable.AddColumn("Rank");
                comparisonTable.AddColumn("Layout");
                comparisonTable.AddColumn("Fitness");
                comparisonTable.AddColumn("Distance");
                comparisonTable.AddColumn("Time");

                for (int i = 0; i < comparisons.Count; i++)
                {
                    var comp = comparisons[i];
                    comparisonTable.AddRow(
                        (i + 1).ToString(),
                        comp.Name,
                        comp.Fitness.ToString("F6"),
                        comp.DistanceComponent.ToString("F3"),
                        comp.TimeComponent.ToString("F3")
                    );
                }

                AnsiConsole.Write(comparisonTable);

                // Show generation history
                if (result.GenerationHistory.Any())
                {
                    AnsiConsole.MarkupLine("\n[bold]Generation Progress:[/]\n");
                    
                    var progressTable = new Table();
                    progressTable.AddColumn("Generation");
                    progressTable.AddColumn("Best Fitness");
                    progressTable.AddColumn("Average Fitness");
                    progressTable.AddColumn("Improvement");
                    
                    double previousBest = double.MaxValue;
                    foreach (var stats in result.GenerationHistory.Take(10))
                    {
                        var improvement = previousBest == double.MaxValue ? "New" : 
                            (stats.BestFitness < previousBest ? "↑" : "→");
                        previousBest = stats.BestFitness;
                        
                        progressTable.AddRow(
                            stats.Generation.ToString(),
                            stats.BestFitness.ToString("F6"),
                            stats.AverageFitness.ToString("F6"),
                            improvement
                        );
                    }
                    
                    AnsiConsole.Write(progressTable);
                }

                // Show key features
                AnsiConsole.MarkupLine("\n[bold]Key Algorithm Features:[/]\n");
                var featuresTable = new Table();
                featuresTable.AddColumn("Feature");
                featuresTable.AddColumn("Description");
                
                featuresTable.AddRow("Population Size", "20 individuals");
                featuresTable.AddRow("Selection", "Tournament selection (k=3)");
                featuresTable.AddRow("Crossover", "Uniform crossover with bias");
                featuresTable.AddRow("Mutation", "Swap mutation (5%)");
                featuresTable.AddRow("Elitism", "Best individuals survive");
                featuresTable.AddRow("Stagnation", "Detection after 5 generations");
                featuresTable.AddRow("Caching", "Fitness result caching");

                AnsiConsole.Write(featuresTable);

                // Show fitness calculation info
                AnsiConsole.MarkupLine("\n[bold]Fitness Calculation:[/]\n");
                AnsiConsole.MarkupLine("The fitness function combines distance and time factors:");
                AnsiConsole.MarkupLine("- [green]Distance Score[/]: Finger travel distance from home position");
                AnsiConsole.MarkupLine("- [blue]Time Score[/]: Typing time including finger penalties");
                AnsiConsole.MarkupLine("- [yellow]Transition Penalty[/]: Extra time for same-hand transitions");
                AnsiConsole.MarkupLine("- [cyan]Formula[/]: Fitness = 0.7 × Distance + 0.3 × Time");

            }
            catch (Exception ex)
            {
                AnsiConsole.MarkupLine($"[bold red]Error: {ex.Message}[/]");
                
                // Show error details
                AnsiConsole.MarkupLine("\n[bold yellow]Error Details:[/]");
                AnsiConsole.MarkupLine($"Exception: {ex.GetType().Name}");
                AnsiConsole.MarkupLine($"Message: {ex.Message}");
                
                if (ex.InnerException != null)
                {
                    AnsiConsole.MarkupLine($"Inner Exception: {ex.InnerException.Message}");
                }
            }
        }
    }
}