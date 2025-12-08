import csv

def write_to_csv(file_path, data, headers):
    with open(file_path, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        for row in data:
            writer.writerow(row)


if __name__ == "__main__":


    
    sample_data = [
        {'Frame': 1, 'X (px)': 150, 'Y (px)': 200, 'X (m)': 0.5, 'Y (m)': 0.75, 'Area': 3000},
        {'Frame': 2, 'X (px)': 160, 'Y (px)': 210, 'X (m)': 0.53, 'Y (m)': 0.78, 'Area': 3200},
        {'Frame': 3, 'X (px)': 170, 'Y (px)': 220, 'X (m)': 0.57, 'Y (m)': 0.82, 'Area': 3500},
    ]
    
    headers = ['Frame', 'X (px)', 'Y (px)', 'X (m)', 'Y (m)', 'Area']
    write_to_csv('tracking_data.csv', sample_data, headers)
    print("Data written to tracking_data.csv")