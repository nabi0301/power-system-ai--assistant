from network_comparison import create_network_comparison
import plotly.io as pio

try:
    print("Creating network comparison figure...")
    fig = create_network_comparison(case_id=1)
    print("Created figure successfully:", type(fig))
    
    # Save the figure to an HTML file
    output_file = "test_comparison.html"
    pio.write_html(fig, output_file)
    print(f"Saved visualization to {output_file}")
    
except Exception as e:
    print("Error creating comparison:", e)