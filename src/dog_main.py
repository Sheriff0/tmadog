import libdogs
import argparse

parser = argparse.ArgumentParser ("submit");
parser.add_argument ('--matno', help = 'Your Matric Number', action
= libdogs.AppendList, dest = libdogs.P_USR);

parser.add_argument ('--pwd', help = 'Your password',
action = libdogs.AppendList, dest = libdogs.P_PWD);

parser.add_argument ('--crscode', help = 'Your target course',
action = libdogs.AppendList, dest = libdogs.P_CRSCODE);

parser.add_argument ('--tma', 
help = 'Your target TMA for the chosen
course', action = libdogs.AppendList, dest = libdogs.P_TMA);

setattr(self, "submit_parser", parser);

