import pandas as pd
import os
import sys


def reverse_complement(dna_seq):
    complement = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C'}
    return ''.join(complement.get(base, base) for base in reversed(dna_seq))


def endswith_ngg(dna_seq):
    return dna_seq[-3] in 'ATCG' and dna_seq[-2:] == 'GG'


def process_dna_sequences(file_path):
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"The file {file_path} does not exist.")
        return

    # Read the Excel file without headers and only the first two columns
    df = pd.read_excel(file_path, header=None, usecols=[0, 1])

    # Set column names
    df.columns = ['name', 'DNA sequence']

    # Debug: Print the DataFrame
    print("Input DataFrame:")
    print(df)

    # Prepare the data for the new Excel file
    data = []
    for index, row in df.iterrows():
        name = row['name']
        dna_seq = str(row['DNA sequence'])

        if pd.isnull(name) or pd.isnull(dna_seq):
            print(f"Skipping row {index + 1} due to missing data.")
            continue

        # Identify NGG at the end and ask user to remove
        if endswith_ngg(dna_seq):
            user_input = input(f"NGG detected at the end of {name}. Do you want to remove NGG? (y/n): ").strip().lower()
            if user_input == 'y':
                dna_seq = dna_seq[:-3]

        rev_comp_seq = reverse_complement(dna_seq)

        # Format the sequences
        formatted_dna_seq = 'CACCG' + dna_seq.lower()
        formatted_rev_comp_seq = 'AAAC' + rev_comp_seq.lower() + 'C'

        data.append([f'{name}-oligo-F', formatted_dna_seq])
        data.append([f'{name}-oligo-R', formatted_rev_comp_seq])

    # Convert the list to a DataFrame
    output_df = pd.DataFrame(data, columns=['Name', 'Sequence'])

    # Write the DataFrame back to the same Excel file but in a new sheet
    with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        output_df.to_excel(writer, index=False, sheet_name='Modified Sequences')

    # Open the Excel file
    os.system(f'start excel.exe "{file_path}"')


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py path_to_your_excel_file.xlsx")
    else:
        file_path = sys.argv[1]
        process_dna_sequences(file_path)
