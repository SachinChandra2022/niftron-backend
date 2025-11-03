# scripts/sync_frontend_assets.py
import os
import shutil
script_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one level to get the backend root
backend_root = os.path.dirname(script_dir)

# Construct the path to the frontend's public directory assuming they are siblings
# e.g., NIFTRON/niftron-backend and NIFTRON/niftron-frontend
frontend_public_dir = os.path.abspath(os.path.join(backend_root, '..', 'niftron-frontend', 'public'))
def sync_assets():
    """
    Copies necessary static assets from the backend context to the frontend's public directory.
    """
    print("--- Syncing assets to frontend ---")
    
    # --- Define Paths ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_root = os.path.dirname(script_dir)
    project_root = os.path.dirname(backend_root) # Assumes backend/frontend are in the same parent folder

    frontend_public_dir = os.path.join(project_root, 'niftron-frontend', 'public')
    
    # We assume generate_plots.py saves files to a 'paper_figures' dir in the backend
    backend_figures_dir = os.path.join(backend_root, 'paper_figures')

    if not os.path.exists(frontend_public_dir):
        print(f"ERROR: Frontend public directory not found at {frontend_public_dir}")
        return

    # --- List of files to sync ---
    files_to_sync = [
        "chart-data.json",
        "equity_curve.png",
        "drawdown_plot.png",
        "feature_importance.png"
    ]

    for file_name in files_to_sync:
        source_path = os.path.join(backend_figures_dir, file_name)
        destination_path = os.path.join(frontend_public_dir, file_name)

        if os.path.exists(source_path):
            print(f"Copying {file_name}...")
            shutil.copy(source_path, destination_path)
        else:
            print(f"WARNING: Source file not found, skipping: {source_path}")

    print("--- Asset sync complete ---")

if __name__ == "__main__":
    sync_assets()