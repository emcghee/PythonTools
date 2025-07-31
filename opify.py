from os import listdir, rename
from os.path import splitext
from random import choice
from argparse import ArgumentParser

def parseArguments():
    parser = ArgumentParser()

    parser.add_argument('--rename', action='store_true')

    return parser.parse_args()

def getBaseName():
    # 28 possibilities
    baseNames = [
        'taxes',
        'appdata',
        'claims',
        'claimdata',
        'forms',
        'formdata',
        'medications',
        'prescriptions',
        'rxdata',
        'treatment',
        'txdata',
        'taxdata',
        'securedata',
        'billingclaims',
        'billinginformation',
        'doctors',
        'nurses',
        'clinicdata',
        'information',
        'info',
        'medicalrecords',
        'medicalforms',
        'dentalrecords',
        'dentaldata',
        'medicalrequirements',
        'allergies',
        'vaccinations',
        'history'
    ]

    return choice(baseNames)

def getCompoundName():
    # 16 * 16 * 5 = 1024
    compoundBase = [
            'claim',
            'tax',
            'app',
            'application',
            'billing',
            'clinic',
            'nurse',
            'doctor',
            'patient',
            'medical',
            'treatment',
            'vaccine',
            'prescription',
            'dental',
            'medical',
            'personal'
        ]

    compoundSuffix = [
        'data',
        'information',
        'specs',
        'info',
        'specifications',
        'record',
        'records',
        'report',
        'note',
        'history',
        'form',
        'chart',
        'requirements',
        'sheet',
        'claim',
        'assessment'
    ]

    return choice(compoundBase) + getLinker() + choice(compoundSuffix)

def getLinker():
    compoundLinker = [
        '_',
        '-',
        '__',
        '.',
        '--'
    ]
    return choice(compoundLinker)

def getRandomNumber():
    # Length 3 - 5
    # 99,900 possibilities
    length = choice(range(3,6))
    number = str()
    for _ in range(length):
        digit = choice(range(10))
        number += str(digit)

    # 50% chance
    chooser = choice(range(2))
    if chooser == 1:
        number = getLinker() + number

    return number

def generateRandomFilename(extension):
    chooser = choice(range(5))
    # 20% chance
    if chooser == 4:
        newName = getBaseName()

    # 80% chance
    else:
        newName = getCompoundName()

    # 67% chance
    chooser = choice(range(3))
    if chooser > 0:
        number = getRandomNumber()
        newName = newName + number
    
    return newName + extension

def main(args):
    willRename = args.rename

    # Ls Current Directory
    files = listdir()

    # For every file map to another
    for file in files:
        _, extension = splitext(file)
        newName = generateRandomFilename(extension)
        if willRename:
            rename(file, newName)

        print(f"{file} -> {newName}")

if __name__ == '__main__':
    args = parseArguments()
    main(args)
