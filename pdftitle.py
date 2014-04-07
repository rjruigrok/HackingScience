#!/usr/bin/env python
# -*- coding: utf-8 -*-

import getopt
import copy
import os
import re
import subprocess
import sys
import traceback
from cStringIO import StringIO
try:
  from lxml import etree
  Parser = etree.XMLParser(recover=True)
except ImportError:
  import xml.etree.ElementTree as etree
  Parser = None


VERSION = '1.1'


def convertPDFToXML(Path):
  """Return XML string of converted PDF file."""
  Cmd = '/usr/local/bin/pdftohtml'
  Args = ['-xml', '-f', '1', '-l', '1', '-i', '-q', '-hidden', '-stdout']
  Process = [Cmd] + Args + [Path]
  XMLString = subprocess.check_output(Process, stderr=open(os.devnull, 'w'))
  if not XMLString:
    ## PDF file can't be found, or is invalid, or is encrypted
    raise EOFError
  return etree.parse(StringIO(removeControlChars(XMLString)), Parser)


def removeControlChars(String):
  """Filter ASCII control characters as etree threats them as invalid"""
  return ''.join([i for i in String if ord(i) in [9, 10, 13] or ord(i) >= 32])


def fontSpecs(XMLData):
  """Return all font specifications in XML."""
  XMLFontSpecs = XMLData.findall('page[@number="1"]/fontspec[@id][@size]')
  return [FS.attrib for FS in XMLFontSpecs]


def sortedFontIds(FontSpecs):
  """Return sorted font specifications by size decending."""
  FontSpecs = sorted(FontSpecs, key=lambda x: int(x['size']), reverse=True)
  return [FS['id'] for FS in FontSpecs]


def textBlocksById(XMLData, FontId):
  """Return text blocks given font id."""
  TextElements = XMLData.findall('page[@number="1"]/text[@font="%s"]' % FontId)
  FirstPageTop = int(XMLData.findall('page[@number="1"]')[0].get('top'))
  FirstPageHeight = int(XMLData.findall('page[@number="1"]')[0].get('height'))
  return topAndTexts(TextElements, FirstPageTop, FirstPageHeight)


def topAndTexts(TextElements, PageTop, PageHeight):
  """Return top position of first non-empty text line and all
  unformatted non-empty text lines, and some extra (page) metadata.
  Example: {
    'pageTop': 0,
    'pageHeight': 1263,
    'blockTop': 16,
    'blockText': [
      {'top': 16, 'height': 24, 'text': 'foo'},
      {'top': 30, 'height': 24, 'text': 'bar'},
      {'top': 44, 'height': 24, 'text': 'baz'}
    ]
  }"""
  TextLines = []
  Top = PageTop

  for TextElement in TextElements:
    TextLine = unformatAndStrip(TextElement)
    if not TextLine:
      continue
    T = int(TextElement.get('top'))
    H = int(TextElement.get('height'))
    W = int(TextElement.get('width'))
    # TODO: Maybe allow a light error here
    # if T < Top - Error:
    # TODO: This is actually a filter
    if T < Top:
      # Ignore text lines positioned upwards. Only look downwards.
      continue
    Top = T
    TextLines.append({
      'top': T,
      'height': H,
      'width': W,
      'text': TextLine
    })

  if TextLines and Top > PageTop:
    return {
      'pageTop': PageTop,
      'pageHeight': PageHeight,
      'blockTop': min(TextLines, key=lambda x: x['top'])['top'],
      'blockText': TextLines
    }
  else:
    return {}


def filterEmpties(TextBlocks, _Config):
  """Filter emtpy text blocks."""
  return [TB for TB in TextBlocks if TB and TB['blockText']]


def unformatAndStrip(TextElement):
  """Return non-empty unformatted text element."""
  return ''.join(TextElement.itertext()).strip()


def filterBottomHalf(TextBlocks, _Config):
  """Filter text blocks on lower half of page."""
  return [TB for TB in TextBlocks if
    TB['blockTop'] - TB['pageTop'] < TB['pageHeight'] / 2]


def filterMargin(TextBlocks, Config):
  """Filter text blocks above certain top margin."""
  return [TB for TB in TextBlocks if TB['blockTop'] > Config['topMargin']]


def filterVertical(TextBlocks, Config):
  """Filter text blocks with vertical text."""
  NewTextBlocks = []
  for TB in TextBlocks:
    NewTB = copy.copy(TB)
    NewTB['blockText'] = []
    for T in TB['blockText']:
      if T['width'] > 0:
        NewTB['blockText'].append(T)
    if NewTB['blockText']:
      NewTextBlocks.append(NewTB)
  return NewTextBlocks


def filterShorts(TextBlocks, Config):
  """Filter text lines which are too short thus unlikely titles."""
  return [TB for TB in TextBlocks if
    len(' '.join([T['text'] for T in TB['blockText']])) >= Config['minLength']]


def filterLongs(TextBlocks, Config):
  """Filter text lines which are too long thus unlikely titles."""
  return [TB for TB in TextBlocks if
    len(' '.join([T['text'] for T in TB['blockText']])) <= Config['maxLength']]


def filterUnrelatedLines(TextBlocks, Config):
  """Filter text lines in text blocks that are too far away from previous
  lines."""
  NewTextBlocks = []
  for TB in TextBlocks:
    NewTB = copy.copy(TB)
    NewTB['blockText'] = []
    NextTop = TB['blockTop']
    for T in TB['blockText']:
      if T['top'] < NextTop + T['height'] / 2:
        NextTop = T['top'] + T['height']
        NewTB['blockText'].append(T)
    if NewTB['blockText']:
      NewTextBlocks.append(NewTB)
  return NewTextBlocks


def title(TextBlocks, Config):
  """Return title as UTF-8 from list. Either all non-empty texts with font id
  or just first."""
  ## Have to encode output when piping script. See: http://goo.gl/h0ql0
  for TB in TextBlocks:
    if Config['multiline']:
      return ' '.join([T['text'] for T in TB['blockText']]).encode('utf-8')
    else:
      return TB['blockText'][0].encode('utf-8')
  return None


def formatUpperCase(Title, _Config):
  """Return the title in titlecase if all letters are uppercase."""
  return Title.title() if isUpperCase(Title) else Title


def isUpperCase(String, Threshold = 0.67):
  """Return True if string has over Threshold uppercase letters, else False."""
  n = 0
  for C in String:
    if C.isupper() or C.isspace():
      n = n+1
  if float(n) / len(String) >= Threshold:
    return True
  else:
    False


def formatWeirdCase(Title, _Config):
  """Return the title in titlecase if all letters are uppercase."""
  return Title.title() if isWeirdCase(Title) else Title


def isWeirdCase(String):
  """Return True if given String has "weird" cases in case letters, else False.
  Example: isWeirdCase('A FAult-tolerAnt token BAsed Algorithm') == True"""
  for i in range(len(String)-2):
    if String[i].isalpha() and (
       String[i+1].isupper() and String[i+2].islower() or
       String[i+1].islower() and String[i+2].isupper()):
      return True
  return False


def formatSpaceCase(Title, _Config):
  """Return the title removing gaps between letters."""
  if isSpaceCase(Title):
    return unspace(Title)
  else:
    return Title


def isSpaceCase(String, Threshold = 0.2):
  """Return True if given String has many gaps between letters, else False.
  Example: isSpaceCase('A H i gh - L e ve l F r am e w or k f or') == True"""
  n = 0
  for C in String:
    if C.isspace():
      n = n+1
  if float(n) / len(String) >= Threshold:
    return True
  else:
    False


def unspace(String):
  """Return the given string without the many gaps between letters.
  Example: unspace('A H i gh - L e ve l F r am e') == A High-Level Frame"""
  JoinedString = ''.join(String.split())
  return re.sub(r'([^-])([A-Z])', r'\1 \2', JoinedString)


def formatMultiSpaces(Title, _Config):
  """Return the title with not more than one space per word separation."""
  # TODO: These are actually two formatters in one
  return ' '.join(Title.split()).replace(' :', ':')


def formatLinebreakDash(Title, _Config):
  """Return the title without linebreak dash."""
  return re.sub(r'(\S)- (.+)', r'\1-\2', Title)


def formatTrailingPeriod(Title, _Config):
  """Return the title without trailing period."""
  return re.sub(r'^(.*)\.$', r'\1', Title)


def formatTrailingAsterik(Title, _Config):
  """Return the title without trailing asterik."""
  return re.sub(r'^(.*)\*$', r'\1', Title)


def formatQuotes(Title, _Config):
  """Return the title with normalized quotes."""
  return Title.replace('‘‘', '“') \
              .replace('’’', '”') \
              .replace('``', '‟') \
              .replace(',,', '„')


# TODO: Generalize functionality to convert Unicode NFD->NFC.
def formatLigatures(Title, _Config):
  """Return the title without Ligatures."""
  # For a reference of the list see: http://typophile.com/files/PMEJLigR_6061.GIF
  # and https://github.com/Docear/PdfUtilities/blob/master/src/org/docear/pdf/util/ReplaceLigaturesFilter.java
  return Title.replace(chr(194)+chr(175), 'fl')


def apply(Funs, Value, Config):
  """Return a value after applying a list of functions until list or value is
  empty."""
  if not (Funs and Value):
    # No more functions to apply or Value (title) was reduced to None
    return Value
  NewValue = Funs[0](Value, Config)
  return apply(Funs[1:], NewValue, Config)


def extractTitle(Path, Config):
  """Return title in PDF article after applying rules and filters."""
  Groupers = [
  ]
  Filters = [
    filterEmpties,
    filterBottomHalf,
    filterMargin,
    filterVertical,
    filterShorts,
    filterLongs,
    filterUnrelatedLines,
    title
  ]
  Formatters = [
    formatLigatures,
    formatUpperCase,
    formatWeirdCase,
    formatSpaceCase,
    formatMultiSpaces,
    formatLinebreakDash,
    formatTrailingPeriod,
    formatTrailingAsterik,
    formatQuotes
  ]
  XMLData = convertPDFToXML(Path)
  FontIds = sortedFontIds(fontSpecs(XMLData))
  TextBlocks = [textBlocksById(XMLData, FontId) for FontId in FontIds]
  Title = apply(Groupers + Filters + Formatters, TextBlocks, Config)
  return Title


def usage():
  Basename = os.path.basename(sys.argv[0])
  return '''Usage: %s [options...] <file>
Options:
 -m, --multiline       Concatenate multiple title lines considered (default)
 -s, --singleline      Only use first title line considered
 -t, --top-margin=<n>  Top margin start to search for title (default: 70)
 -n, --min-length=<n>  Min. considerable title length (default: 15)
 -x, --max-length=<n>  Max. considerable title length (default: 250)
 -d, --debug           Print error stacktrace for unknown errors
 -v, --version         Show version info
 -h, --help            Show usage screen''' % Basename


def exit(Code, Str):
  if Code:
    sys.stderr.write(Str + '\n')
  else:
    print Str
  return Code


def main(Argv=None):
  """Find first non-empty text in PDF File with largest size and return as
  unformatted string."""
  Argv = Argv or sys.argv[1:]

  ## Argument parsing
  try:
    LongOpts = ['help', 'version', 'multiline', 'singleline', 'top-margin=',
                'min-length=', 'max-length=', 'debug']
    Opts, Args = getopt.getopt(Argv, 'hvdmst:n:x:', LongOpts)
  except getopt.GetoptError as err:
    return exit(2, str(err) + '\n' + usage())

  Multiline = True
  TopMargin = 70
  MinLength = 15
  MaxLength = 250
  Debug = False

  try:
    for o, a in Opts:
      if (o in ['-h', '--help']):
        return exit(0, usage())
      elif (o in ['-v', '--version']):
        return exit(0, VERSION)
      elif (o in ['-d', '--debug']):
        Debug = True
      elif (o in ['-m', '--multiline']):
        Multiline = True
      elif (o in ['-s', '--singleline']):
        Multiline = False
      elif (o in ['-t', '--top-margin']):
        TopMargin = int(a)
        if TopMargin < 0:
          raise AssertionError
      elif (o in ['-n', '--min-length']):
        MinLength = int(a)
        if MinLength < 0:
          raise AssertionError
      elif (o in ['-x', '--max-length']):
        MaxLength = int(a)
        if MaxLength < 0:
          raise AssertionError
      else:
        return exit(2, 'Invalid argument')

    Config = {
      'multiline': Multiline,
      'topMargin': TopMargin,
      'minLength': MinLength,
      'maxLength': MaxLength,
      'debug': Debug
    }

    if not len(Args):
      return exit(2, usage())
    Path = Args[0]
    if not os.path.isfile(Path):
      raise IOError
    Title = extractTitle(Path, Config)
    if not Title:
      return exit(1, 'No title found')
    else:
      print Title
  except AssertionError as e:
    return exit(2, 'Invalid argument value' + '\n' + usage())
  except IOError:
    return exit(3, 'No such file')
  except OSError:
    return exit(4, 'pdftohtml not found')
  except EOFError:
    return exit(5, 'Could not convert PDF to XML')
  except etree.ParseError:
    return exit(6, 'Could not parse XML')
  except:
    if Debug:
      traceback.print_exc()
    return exit(8, 'Unknown error')

if __name__ == '__main__':
  sys.exit(main())
