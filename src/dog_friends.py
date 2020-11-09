import argparse


def submit():
    parser = argparse.ArgumentParser ("submit");
    parser.add_argument ('--matno', help = 'Your Matric Number', action = 'append')

    parser.add_argument ('--pwd', help = 'Your password',
            action = 'append')

    parser.add_argument ('--crscode', help = 'Your target course', action = 'append')

    parser.add_argument ('--tma', help = 'Your target TMA for the chosen course', action = 'append')

    
            
    def _submit(dog, args):
        pass;

    return _submit;
