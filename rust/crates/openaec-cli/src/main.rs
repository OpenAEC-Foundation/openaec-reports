use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "openaec-cli")]
#[command(about = "OpenAEC Report Generator CLI")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Generate a PDF report from JSON data
    Generate {
        /// Path to JSON report data
        #[arg(short, long)]
        data: String,

        /// Output PDF path
        #[arg(short, long)]
        output: String,

        /// Tenant directory (overrides OPENAEC_TENANT_DIR)
        #[arg(long)]
        tenant_dir: Option<String>,
    },

    /// Validate JSON report data against the schema
    Validate {
        /// Path to JSON report data
        #[arg(short, long)]
        data: String,
    },

    /// Start the API server
    Serve {
        /// Port to listen on
        #[arg(short, long, default_value = "8000")]
        port: u16,
    },
}

fn main() {
    let cli = Cli::parse();

    match cli.command {
        Commands::Generate { data, output, .. } => {
            println!("Generate: {data} -> {output} (not yet implemented)");
        }
        Commands::Validate { data } => {
            println!("Validate: {data} (not yet implemented)");
        }
        Commands::Serve { port } => {
            println!("Serve on port {port} (not yet implemented)");
        }
    }
}
