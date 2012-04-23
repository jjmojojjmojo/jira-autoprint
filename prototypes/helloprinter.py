"""
autoprint - a simple JSON interface to print 'directly' to a printer via CUPS

Prototype 1 - PDF Generation And Print

Generates a PDF and prints it to the default print queue.
"""

import cups, os
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth, getFont
from reportlab.lib.colors import pink, black, red, blue, green, lightgrey
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter

# path to the file we'll generate and print
# @TODO: in the final app, do this in a temp file.
# @TODO: should there be an option to hold on to the files?
output = "hello.pdf"

font = "Helvetica"
size = 24

def float_range(start, end, increment, cap=True):
    """
    like the built-in range(), but supports floats.
    
    :param cap: boolean, set to true to add the end value to the list.
    """
    result = []
    idx = start
    while idx <= end:
        print idx
        result.append(idx)
        idx = idx+increment
    
    if cap:
        result.append(end)
        
    return result

def telemetry(font, size):
    """
    Return information about a given font.
    
    Returns a dict, with the following members:
    { 
      'm_width': float, approximated 'em square' size (rough),
      'ascent': float, maximum height of text above baseline,
      'descent': float, maxmim height of text below baseline,
      'max_height': float, ascent+descent
    }
    """
    face = getFont(font).face
    
    # +30% 'fudge' factor
    m_width = stringWidth('M', font, size)*1.3
    
    ascent = float(face.ascent)*m_width/1000       
    descent = float(face.descent*-1)*m_width/1000
    
    return {
        'm_width': m_width,
        'ascent': ascent,
        'descent': descent,
        'max_height': ascent+descent,
    }

def print_centered_text(canvas_obj, text, page_width, page_height, font, size):
    """
    Draw some text centered on the page
    """
    string_width = stringWidth(text, font, size)
    
    info = telemetry(font, size)
    
    x = (page_width/2)-(string_width/2)
    y = (page_height/2)-(info['max_height']/2)
    
    canvas_obj.drawString(x,y,text)


try:
    # connect to the default cups server
    connection = cups.Connection()
    
    # not used here, but useful to have a list of printers 
    # so the user can select one
    printers = connection.getPrinters()
    
    # get the default printer - this is just a name
    printer = connection.getDefault()
    
    # get the default margins
    # @todo: can we get the page size and map that to reportlab size specs?
    
    # first get the printer def file
    ppd_path = connection.getPPD(printer)
    ppd_obj = cups.PPD(ppd_path)
    
    # now extract the default margins
    # TODO: my printer returns values without units, the spec says units are possible
    # TODO: what the PPD file says, and what my printer will use aren't the same :(
    margins = [int(x) for x in ppd_obj.findAttr('HWMargins').value.split()]
    
    margin_left, margin_bottom, margin_right, margin_top = margins
    
    # incorporate margins
    page_width, page_height = letter
    # page_width = page_width-(margin_left+margin_right)
    # page_height = page_height-(margin_top+margin_bottom)
    
    c = canvas.Canvas(output, pagesize=letter)
    
    # 1/4" grid to check positioning
    c.setStrokeColor(lightgrey)
    #c.grid(float_range(margin_left, page_width-(margin_left+margin_right), inch*0.25), float_range(margin_bottom, page_height-(margin_top+margin_bottom), inch*0.25))
    c.rect(margin_left, margin_bottom, page_width-(margin_left+margin_right), page_height-(margin_top+margin_bottom))
    
    c.setFont(font, size)
    
    print_centered_text(c, "Printed From Python", page_width, page_height, font, size)
    
    c.showPage()
    c.save()
    
    
    # set some options - these seem to correspond to what
    # lp/lpr will take on the command line (see the output of `lproptions -l)
    # 
    # You can query the printer for available options like so:
    available_options = connection.getPrinterAttributes(printer)['job-creation-attributes-supported']
    
    # not all options that you can set from the print dialog from most desktop apps
    # will be available. 
    # @TODO: need to figure out how to provide a more typical job configuration dialog to users
    #
    
    # print the file - all of these options are required
    connection.printFile(
        title="Test Print",    # title
        printer=printer,       # the printer to use (it's name)
        filename=output,       # file to print
        options={},            # options - from  'job-creation-attributes-supported' above, if needed.
    )
    
finally:
  # remove the file
  if os.path.exists(output):
      os.remove(output)
