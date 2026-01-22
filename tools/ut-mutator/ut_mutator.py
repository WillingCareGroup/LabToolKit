import argparse

def ut_mutator(rna_sequence):
    """
    Converts an RNA sequence to a DNA sequence by replacing all occurrences of 'U' with 'T'.

    Args:
        rna_sequence (str): RNA sequence to convert.

    Returns:
        str: DNA sequence with 'U' replaced by 'T'.
    """
    dna_sequence = rna_sequence.replace('U', 'T')
    return dna_sequence

def main():
    parser = argparse.ArgumentParser(description='Converts an RNA sequence to a DNA sequence by replacing all occurrences of "U" with "T"')
    parser.add_argument('-i', '--input', help='RNA sequence to convert')
    args = parser.parse_args()

    rna_sequence = args.input if args.input else input("Enter an RNA sequence: ")
    dna_sequence = ut_mutator(rna_sequence)
    print("DNA sequence: ", dna_sequence)

if __name__ == '__main__':
    main()