from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth, getFont
from reportlab.lib.colors import pink, black, red, blue, green, lightgrey
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter

output = "center.pdf"
message = "Printed From Python"

font = "Helvetica"
size = 24
c = canvas.Canvas(output, pagesize=letter) 

page_width, page_height = letter

# add a grid to help visually check the alignment
def float_range(start, end, increment):
    result = []
    idx = start
    while idx <= end:
        print idx
        result.append(idx);
        idx = idx+increment
        
        
    return result

c.setStrokeColor(lightgrey)
c.grid(float_range(0, page_width, inch*0.25), float_range(0, page_height, inch*0.25))

c.setFont(font, size)

# do some math
string_width = stringWidth(message, font, size)

# string height is nuanced - we'll take a cue from the designer and get 
# close 
# @see: http://two.pairlist.net/pipermail/reportlab-users/2009-March/008131.html
face = getFont(font).face
# ascent/descent is measured in em-square 1000ths
# adding 30% fudges it since that measure isn't exactly the width of a capital M.
m_width = stringWidth('M', font, size)*1.3

# returned in 1000ths of the width of 'm'
ascent = float(face.ascent)*m_width/1000         # the distance the font can go above the baseline
descent = float(face.descent*-1)*m_width/1000       # the distance the font can go below the baseline

# so the maximum height of a theoretical bounding box of the font at this size 
# would be ascent+descent, but since most of the string goes above the baseline,
# we'll just use that.
max_height = ascent+descent

x = (page_width/2)-(string_width/2)
y = (page_height/2)-(max_height/2)

print "Ascent: %s (orig: %s)" % (ascent, face.ascent)
print "Descent: %s (orig: %s)" % (descent, face.descent)
print "Max Heigt: %s" % (max_height)

c.drawString(x,y,message)

# draw a box around the text to help with visual alignment
c.setStrokeColor(black)
padding = 0
c.rect(x-padding, y-descent-padding, string_width+(padding*2), max_height+(padding*2))

c.showPage()
c.save()
