f = "TAAtccctatcagtgatagagaGAGAGTGTTAGAACTGGtccctatcagtgatagagaACGTGCGGTTTCTCTGCtccctatcagtgatagagaGAAGAACACCTCGAGCTtccctatcagtgatagagaGTTGCGTTGTTGCGCTGtccctatcagtgatagagaCCTAGATGCAGTGTCGCtccctatcagtgatagagaACATATCACTTTTGCTTtccctatcagtgatagagaacggctaggcgtgtacggtgggaggcctatataagcagagctcgtttagtgaaccgtcagatcgcaccggtGGTACCgccaccatggggagcagcaagagcaagcccaaggaccccagccagcg"
r = "ccggcgctggctggggtccttgggcttgctcttgctgctccccatggtggcGGTACCaccggtgcgatctgacggttcactaaacgagctctgcttatataggcctcccaccgtacacgcctagccgttctctatcactgatagggaAAGCAAAAGTGATATGTtctctatcactgatagggaGCGACACTGCATCTAGGtctctatcactgaz"+"tagggaCAGCGCAACAACGCAACtctctatcactgatagggaAGCTCGAGGTGTTCTTCtctctatcactgatagggaGCAGAGAAACCGCACGTtctctatcactgatagggaCCAGTTCTAACACTCTCtctctatcactgatagggaTTAAT"

def ChopSeq(a, b, c):
    primerlistf = []  # Initialize the list to store forward sequences
    primerlistr = []  # Initialize the list to store reverse sequences
    n = c  # Define the chunk size

    # Handle forward primers
    for i in range(0, len(a), n):
        temp = a[i:i+n]
        primerlistf.append(temp)

    # Handle reverse primers
    for i in range(0, len(b), n):
        temp = b[i:i+n]
        primerlistr.append(temp)
    primerlistr = list(reversed(primerlistr))  # Reverse the list after it's fully populated

    # Write both forward and reverse primers to the same file
    filename = 'Primers_output.txt'
    with open(filename, 'w') as file:
        # Write forward primers with label 'F'
        for index, primer in enumerate(primerlistf, 1):
            file.write(f'{index}F\t{primer}\n')
        # Write reverse primers with label 'R'
        for index, primer in enumerate(primerlistr, 1):
            file.write(f'{index}R\t{primer}\n')

    print(f"File '{filename}' has been written successfully.")



ChopSeq(f,r,37)

