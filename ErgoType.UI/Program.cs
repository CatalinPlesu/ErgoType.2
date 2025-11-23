namespace ErgoType.UI;

using ErgoType.Core;
using ErgoType.Core.Fitness;
using Spectre.Console;

/// <summary>
/// Main console application for keyboard layout optimization.
/// </summary>
public class Program
{
    /// <summary>
    /// Main entry point.
    /// </summary>
    public static void Main(string[] args)
    {
        Console.Clear();
        ShowHeader();
        
        if (args.Contains("--demo"))
        {
            RunDemo();
            return;
        }
        
        var choice = ShowMainMenu();
        
        switch (choice)
        {
            case "optimize":
                RunOptimization();
                break;
            case "compare":
                RunComparison();
                break;
            case "evaluate":
                RunEvaluation();
                break;
            case "demo":
                RunDemo();
                break;
            case "exit":
                return;
        }
        
        // Continue until user chooses to exit
        do
        {
            choice = ShowMainMenu();
            
            switch (choice)
            {
                case "optimize":
                    RunOptimization();
                    break;
                case "compare":
                    RunComparison();
                    break;
                case "evaluate":
                    RunEvaluation();
                    break;
                case "demo":
                    RunDemo();
                    break;
            }
        }
        while (choice != "exit");
    }
    
    /// <summary>
    /// Shows the main header.
    /// </summary>
    private static void ShowHeader()
    {
        AnsiConsole.Write(
            new FigletText("ErgoType")
                .Centered()
                .Color(Color.Cyan1));
                
        AnsiConsole.WriteLine();
        AnsiConsole.WriteLine("Keyboard Layout Optimization System".PadCenter(80));
        AnsiConsole.WriteLine("=".PadRight(80, '='));
        AnsiConsole.WriteLine();
    }
    
    /// <summary>
    /// Shows the main menu and returns user choice.
    /// </summary>
    private static string ShowMainMenu()
    {
        return AnsiConsole.Prompt(
            new SelectionPrompt<string>()
                .Title("What would you like to do?")
                .PageSize(10)
                .AddChoices(new[]
                {
                    "optimize",
                    "compare", 
                    "evaluate",
                    "demo",
                    "exit"
                })
                .UseConverter(choice => choice switch
                {
                    "optimize" => "[bold]Optimize[/] - Run genetic algorithm optimization",
                    "compare" => "[bold]Compare[/] - Compare existing keyboard layouts",
                    "evaluate" => "[bold]Evaluate[/] - Evaluate a single layout",
                    "demo" => "[bold]Demo[/] - Run demonstration",
                    "exit" => "[bold]Exit[/] - Quit the application",
                    _ => choice
                }));
    }
    
    /// <summary>
    /// Runs the optimization workflow.
    /// </summary>
    private static void RunOptimization()
    {
        Console.Clear();
        ShowHeader();
        
        AnsiConsole.MarkupLine("[bold cyan]Genetic Algorithm Optimization[/]");
        AnsiConsole.WriteLine();
        
        // Get optimization parameters
        var config = GetOptimizationConfig();
        var optimizer = new KeyboardLayoutOptimizer(config);
        
        AnsiConsole.WriteLine("Starting optimization...");
        AnsiConsole.WriteLine();
        
        try
        {
            var result = optimizer.Optimize();
            
            // Show results
            ShowOptimizationResults(result);
        }
        catch (Exception ex)
        {
            AnsiConsole.MarkupLine("[red]Error during optimization:[/] " + ex.Message);
        }
        
        AnsiConsole.WriteLine();
        AnsiConsole.Prompt(
            new TextPrompt<string>("Press [bold]Enter[/] to continue...")
                .AllowEmpty());
    }
    
    /// <summary>
    /// Runs the layout comparison workflow.
    /// </summary>
    private static void RunComparison()
    {
        Console.Clear();
        ShowHeader();
        
        AnsiConsole.MarkupLine("[bold cyan]Layout Comparison[/]");
        AnsiConsole.WriteLine();
        
        var layouts = AnsiConsole.Prompt(
            new MultiSelectionPrompt<string>()
                .Title("Select layouts to compare:")
                .PageSize(10)
                .AddChoices(GetAvailableLayouts())
                .Required());
        
        if (!layouts.Any())
        {
            AnsiConsole.MarkupLine("[yellow]No layouts selected.[/]");
            return;
        }
        
        var config = GetBasicConfig();
        var optimizer = new KeyboardLayoutOptimizer(config);
        
        AnsiConsole.WriteLine("Comparing layouts...");
        
        try
        {
            var results = optimizer.CompareLayouts(layouts.ToArray());
            ShowComparisonResults(results);
        }
        catch (Exception ex)
        {
            AnsiConsole.MarkupLine("[red]Error during comparison:[/] " + ex.Message);
        }
        
        AnsiConsole.WriteLine();
        AnsiConsole.Prompt(
            new TextPrompt<string>("Press [bold]Enter[/] to continue...")
                .AllowEmpty());
    }
    
    /// <summary>
    /// Runs the layout evaluation workflow.
    /// </summary>
    private static void RunEvaluation()
    {
        Console.Clear();
        ShowHeader();
        
        AnsiConsole.MarkupLine("[bold cyan]Layout Evaluation[/]");
        AnsiConsole.WriteLine();
        
        var layoutName = AnsiConsole.Prompt(
            new SelectionPrompt<string>()
                .Title("Select a layout to evaluate:")
                .AddChoices(GetAvailableLayouts()));
        
        var config = GetBasicConfig();
        var optimizer = new KeyboardLayoutOptimizer(config);
        
        AnsiConsole.WriteLine("Evaluating layout...");
        
        try
        {
            var layout = GetLayoutByName(layoutName);
            if (layout is not null)
            {
                var result = optimizer.EvaluateLayout(layout);
                ShowEvaluationResult(layoutName, result);
            }
        }
        catch (Exception ex)
        {
            AnsiConsole.MarkupLine("[red]Error during evaluation:[/] " + ex.Message);
        }
        
        AnsiConsole.WriteLine();
        AnsiConsole.Prompt(
            new TextPrompt<string>("Press [bold]Enter[/] to continue...")
                .AllowEmpty());
    }
    
    /// <summary>
    /// Runs the demonstration.
    /// </summary>
    private static void RunDemo()
    {
        Console.Clear();
        ShowHeader();
        
        AnsiConsole.MarkupLine("[bold cyan]Demo Mode[/]");
        AnsiConsole.WriteLine();
        
        // Demo configuration
        var config = new OptimizationConfig
        {
            GAConfig = new GAConfig
            {
                PopulationSize = 20,
                MaxGenerations = 15,
                TournamentSize = 3,
                MutationRate = 0.05,
                StagnationLimit = 5,
                EliteCount = 3
            },
            FitnessConfig = new FitnessConfig
            {
                DistanceWeight = 0.7,
                TimeWeight = 0.3,
                UseSimplifiedFitness = true
            },
            Verbose = true
        };
        
        var optimizer = new KeyboardLayoutOptimizer(config);
        
        // Show comparison of existing layouts first
        AnsiConsole.MarkupLine("[bold]Comparing existing layouts...[/]");
        var comparisonResults = optimizer.CompareLayouts("QWERTY", "Dvorak", "Colemak", "Workman");
        ShowComparisonResults(comparisonResults);
        
        AnsiConsole.WriteLine();
        AnsiConsole.MarkupLine("[bold]Running genetic algorithm optimization...[/]");
        
        try
        {
            var result = optimizer.Optimize();
            ShowOptimizationResults(result);
        }
        catch (Exception ex)
        {
            AnsiConsole.MarkupLine("[red]Error during demo:[/] " + ex.Message);
        }
        
        AnsiConsole.WriteLine();
        AnsiConsole.Prompt(
            new TextPrompt<string>("Press [bold]Enter[/] to continue...")
                .AllowEmpty());
    }
    
    /// <summary>
    /// Gets optimization configuration from user input.
    /// </summary>
    private static OptimizationConfig GetOptimizationConfig()
    {
        var populationSize = AnsiConsole.Prompt(
            new TextPrompt<int>("Population size?")
                .DefaultValue(50)
                .Validate(value => value >= 10 ? ValidationResult.Success() 
                                              : ValidationResult.Error("[red]Must be at least 10[/]")));
        
        var maxGenerations = AnsiConsole.Prompt(
            new TextPrompt<int>("Max generations?")
                .DefaultValue(100)
                .Validate(value => value >= 1 ? ValidationResult.Success() 
                                              : ValidationResult.Error("[red]Must be at least 1[/]")));
        
        var keyboardLayout = AnsiConsole.Prompt(
            new SelectionPrompt<string>()
                .Title("Keyboard layout:")
                .AddChoices(new[] { "ANSI 60%", "Dactyl ManuForm", "Ferris Sweep" }));
        
        var distanceWeight = AnsiConsole.Prompt(
            new TextPrompt<double>("Distance weight (0.0-1.0)?")
                .DefaultValue(0.7)
                .Validate(value => value >= 0 && value <= 1 ? ValidationResult.Success() 
                                                              : ValidationResult.Error("[red]Must be between 0.0 and 1.0[/]")));
        
        return new OptimizationConfig
        {
            GAConfig = new GAConfig
            {
                PopulationSize = populationSize,
                MaxGenerations = maxGenerations
            },
            FitnessConfig = new FitnessConfig
            {
                DistanceWeight = distanceWeight,
                TimeWeight = 1.0 - distanceWeight
            },
            KeyboardLayout = keyboardLayout.Replace(" ", "_")
        };
    }
    
    /// <summary>
    /// Gets basic configuration.
    /// </summary>
    private static OptimizationConfig GetBasicConfig() => new();
    
    /// <summary>
    /// Gets available layout names.
    /// </summary>
    private static string[] GetAvailableLayouts() => new[]
    {
        "QWERTY", "Dvorak", "Colemak", "Workman", "Asset", "Norman", "Minimak"
    };
    
    /// <summary>
    /// Gets a layout by name.
    /// </summary>
    private static KeyboardLayout? GetLayoutByName(string name)
    {
        return name.ToLower() switch
        {
            "qwerty" => KeyboardLayout.Create("qwerty", "qwertyuiopasdfghjklzxcvbnm".ToCharArray()),
            "dvorak" => KeyboardLayout.Create("dvorak", "pyfgcrlaoeuidhtnsqjkxbmwvz".ToCharArray()),
            "colemak" => KeyboardLayout.Create("colemak", "qwfpgjluyarstdhneiozxcvmbk".ToCharArray()),
            "workman" => KeyboardLayout.Create("workman", "qdrwypfujelsiozhaxngctmbvk".ToCharArray()),
            "asset" => KeyboardLayout.Create("asset", "amswfdtugnelkhirozcypbqvjx".ToCharArray()),
            "norman" => KeyboardLayout.Create("norman", "qwfpgjluyarasdhtneoizxcdvbm".ToCharArray()),
            "minimak" => KeyboardLayout.Create("minimak", "qwfpgjluyarstdhneiozxcvbm".ToCharArray()),
            _ => null
        };
    }
    
    /// <summary>
    /// Shows optimization results.
    /// </summary>
    private static void ShowOptimizationResults(GAResult result)
    {
        AnsiConsole.WriteLine();
        AnsiConsole.MarkupLine("[bold green]Optimization Results:[/]");
        
        var table = new Table();
        table.AddColumn("[bold]Metric[/]");
        table.AddColumn("[bold]Value[/]");
        
        table.AddRow("Best Layout", result.BestIndividual.Name);
        table.AddRow("Fitness Score", result.BestIndividual.Fitness?.ToString("F6") ?? "N/A");
        table.AddRow("Generations", result.Generations.ToString());
        table.AddRow("Execution Time", $"{result.ExecutionTimeMs:F0}ms");
        table.AddRow("Stagnated", result.Stagnated ? "Yes" : "No");
        table.AddRow("Layout", new string(result.BestIndividual.Layout.Chromosome));
        
        AnsiConsole.Write(table);
    }
    
    /// <summary>
    /// Shows comparison results.
    /// </summary>
    private static void ShowComparisonResults(Dictionary<string, Fitness.FitnessResult> results)
    {
        AnsiConsole.WriteLine();
        AnsiConsole.MarkupLine("[bold green]Comparison Results:[/]");
        
        var table = new Table();
        table.AddColumn("[bold]Layout[/]");
        table.AddColumn("[bold]Fitness[/]");
        table.AddColumn("[bold]Distance[/]");
        table.AddColumn("[bold]Time[/]");
        table.AddColumn("[bold]Calculation Time[/]");
        
        foreach (var kvp in results.OrderByDescending(kvp => kvp.Value.Fitness))
        {
            table.AddRow(
                kvp.Key,
                kvp.Value.Fitness.ToString("F6"),
                kvp.Value.DistanceScore.ToString("F1"),
                kvp.Value.TimeScore.ToString("F1"),
                $"{kvp.Value.CalculationTimeMs:F0}ms"
            );
        }
        
        AnsiConsole.Write(table);
    }
    
    /// <summary>
    /// Shows evaluation result.
    /// </summary>
    private static void ShowEvaluationResult(string layoutName, Fitness.FitnessResult result)
    {
        AnsiConsole.WriteLine();
        AnsiConsole.MarkupLine($"[bold green]Evaluation Results for {layoutName}:[/]");
        
        var table = new Table();
        table.AddColumn("[bold]Metric[/]");
        table.AddColumn("[bold]Value[/]");
        
        table.AddRow("Fitness Score", result.Fitness.ToString("F6"));
        table.AddRow("Distance Score", result.DistanceScore.ToString("F1"));
        table.AddRow("Time Score", result.TimeScore.ToString("F1"));
        table.AddRow("Calculation Time", $"{result.CalculationTimeMs:F0}ms");
        
        AnsiConsole.Write(table);
    }
}