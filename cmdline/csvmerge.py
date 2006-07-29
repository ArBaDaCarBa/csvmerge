#! /usr/bin/env python

# Merges two csv files based on a column identity
# $Id: csvmerge.py,v 1.9 2003/12/01 15:39:28 bertrand Exp $

import sys, csv
from optparse import OptionParser

class WritableNextableList(list):
    """Add the write method to a list
    """
    def write(self, stuff):
        self.append(stuff)

    def next(self):
        try:
            self._pos += 1
        except AttributeError:
            self._pos = 1
        if self._pos > len(self):
            raise StopIteration()
        return self[self._pos - 1]
    
def ab_to_12(ab_value):
    """Convert A, B, C, ...AA, AB, ... HJ, HK... notation to numeric index

    ab_value -- AB column notation
    """
    value = 0
    for c in ab_value.upper(): # Going thru the text
        value = value * 26
        value = value + ord(c) - 64 # 64 = ord('A') - 1
    return value

def findCommonColumnList(data1, data2, column1, column2):
    """Find common column values between two lists of lists.

    data1 -- for list of list

    data2 -- second list of list

    column1 -- index of column for data1

    column2 -- index of column for data2

    returns a list of common values
    """

    # Create index of values
    values1 = [ elmnt[column1] for elmnt in data1 ]
    values2 = [ elmnt[column2] for elmnt in data2 ]

    return [ elmnt for elmnt in values1 if elmnt in values2 ]

def csv2array(handler):
    """Reads a file and returns a array with all the data

    handler -- file handler
    """
    ret = []
    
    # Reading the file
    csv_reader = csv.reader(handler)
    
    for line in csv_reader:
        ret.append(line)

    return ret

def getMaxLength(array):
    """returns length of the longer line in the array

    array -- list of lists
    """
    return max( [ len(el) for el in array ] )

def normalizeArray(array, max_length=None):
    """Normalize the size of each array line

    array -- list of lists

    max_length -- maximum size of a line. If none, will be computed
    """
    if not max_length:
        max_length = getMaxLength(array)

    for line in array:
        line += [''] * (max_length - len(line))
        
def makeIndexedDict(array, column, options):
    """Create a dictionnary {column_value: line,...}
    **BE CAREFUL WITH DUPLICATES!!!**
    
    array -- list of lists

    column -- column number to be the index

    options -- options dictionary
    """
    ret = {}

    for line in array:
        key = line[column].strip()
        if ret.has_key(key):
            # key already exists
            if options['stop']:
                # must stop ?
                raise 'HAS DUPLICATE KEY'
            elif options['first']:
                # must keep existing ?
                continue
        ret[key] = line

    return ret

def csvmerge(handler1, handler2, set_options={}):
    """Merges 2 CSV files

    handler1 -- handler on file 1

    handler2 -- handler on file 2

    options -- dictionnary with options (There are some default options so you
               don't have to set everything):
       column1 - index of reference column in file 1* (0)
       column2 - index of reference column in file 2* (0)
       stop - 0 or 1, stops when duplication found within a file (0)
       first - 0 or 1, if duplicates, keep the first instance, or the last (0)
       format - string describing the output format ('1.*,2.*')
       only - keep common (0) or differences (1 or 2) (0)

       * Starts with 0
    """    
    # Creating arrays
    array1 = csv2array(handler1)
    array2 = csv2array(handler2)
    merge = WritableNextableList()
    csv_writer = csv.writer(merge)

    # Merging default options with new options
    options = {
        'column1': 0,
        'column2': 0,
        'stop': 0,
        'first': 0,
        'format': '1.*,2.*',
        'only': 0
        }
    options.update(set_options)
    
    # Getting max length
    len1 = getMaxLength(array1)
    len2 = getMaxLength(array2)

    # Normalizing size for bogus CSV files
    normalizeArray(array1, len1)
    normalizeArray(array2, len2)

    # Creating dictionary for 2nd file
    dict2 = makeIndexedDict(array2, options['column2'], options)
    
    # Finding te commond elements
    commonList = findCommonColumnList(array1, array2, options['column1'],
                                      options['column2'])

    # Merging arrays
    if options['only'] < 2:
        # Common or first file only
        for line in array1:
            idx = line[options['column1']].strip()
            if idx in commonList:
                if options['only'] == 0:
                    # in common, and display common
                    csv_writer.writerow(
                        formatList(line, dict2[idx], options['format']))
            elif options['only'] == 1: # not in commonList
                # only in first file
                csv_writer.writerow(
                    formatList(line, [''] * len2, options['format']))
    else:
        # Second file only
        for line in array2:
            idx = line[options['column2']].strip()
            if idx not in commonList:
                csv_writer.writerow(
                    formatList([''] * len1, line, options['format']))

    return merge

def formatList(list1, list2, format):
    """Ouput a formated list, merging the 2 lists

    list1 -- first list

    list2 -- second list

    format -- GNU join type format
    """
    worklist = (list1, list2)
    ret = []

    for elmnt in csv.reader(WritableNextableList([format])).next():

        listnum, colnum = elmnt.split('.')
        listnum = eval(listnum) - 1

        if colnum == '*':
            ret += worklist[listnum]
        else:
            ret.append(worklist[listnum][eval(colnum) - 1])

    return ret

def createOptionParser():
    """Creates the options parser
    """
    # Option parser
    usage = '''usage: %prog -1 column1 -2 column2 [-o n.m,...] [--first|--last]
                   [--stop] [--only [1|2]] file1 file2

    Merges two CSV files in a GNU join way.
    '''
    opt = OptionParser(usage=usage)
    opt.add_option('-1', dest='column1',
                   help='column of first file (starts at 1)',
                   metavar=' column1')
    opt.add_option('-2', dest='column2',
                   help='column of second file (starts at 1)',
                   metavar=' column2')
    opt.add_option('-o', dest='format', default='1.*,2.*',
                   help='''Ouput format, comma separated values of n.m where
                   n is the file number an m the field number.
                   Default is 1.*,2.* = display all fields in both files''',
                   metavar=' n.m,...')
    opt.add_option('--stop', dest='stop', action='store_true', default=0,
                   help='''do not continue if duplicate is found within one
                   file''')
    opt.add_option('--first', dest='first', action='store_true', default=1,
                   help='''in case of duplicate within one file, use first
                   instance (default)''')
    opt.add_option('--last', dest='first', action='store_false',
                    help='opposite to --first, keep last instance')
    opt.add_option('--only', dest='only', type='int', default=0,
                   help='show only elements in file 1 or 2',
                   metavar='1|2')

    return opt

if __name__ == '__main__':
    # Option parser
    opt = createOptionParser()
    
    # Parsing, and checking
    (options, args) = opt.parse_args()

    if len(args) != 2:
        opt.error('you must specify TWO files !')

    if not options.column1 or not options.column2:
        opt.error('you must specify columns for the two files !')

    # Checking if columns are in digit or letter
    try:
        options.column1 = eval(options.column1)
    except:
        options.column1 = ab_to_12(options.column1)

    try:
        options.column2 = eval(options.column2)
    except:
        options.column2 = ab_to_12(options.column2)

    if options.only not in [0, 1, 2]:
        opt.error('only must be 1 or 2 !')
        
    merge = csvmerge(open(args[0]), open(args[1]), {
        'column1' : options.column1 - 1, 'column2' : options.column2 - 1,
        'stop' : options.stop, 'first': options.first,
        'format': options.format, 'only': options.only,
        })
                                       
    for line in merge:
        print line.strip()
