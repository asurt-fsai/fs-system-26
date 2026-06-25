import sys
import pandas as pd
import matplotlib.pyplot as plt

def main(csv_file):
    # Read the CSV file without headers
    try:
        df = pd.read_csv(csv_file, header=None)
    except Exception as e:
        print(f"Error reading {csv_file}: {e}")
        sys.exit(1)
    
    # Check if the CSV has at least two columns
    if df.shape[1] < 2:
        print("CSV file must have at least two columns.")
        sys.exit(1)
    
    # Use the first column as x and the second column as y
    x = df.iloc[:, 0]
    y = df.iloc[:, 1]
    
    # Plot the coordinates
    plt.figure(figsize=(8, 6))
    plt.scatter(x, y, c='blue', marker='o')
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.title("Coordinate Plot")
    plt.grid(True)
    plt.show()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python script.py <full_path_to_csv_file>")
        sys.exit(1)
    csv_file = sys.argv[1]
    main(csv_file)
