#!python2

from __future__ import print_function

# use TCP (no configuration of DCS-BIOS required, but the
# script needs to be started after getting into the cockpit)

#CONNECTION = {
#        "type":"TCP",
#        "host":"172.16.1.2", # IP address of DCS computer
#        "port":7778
#        }


# use UDP (configure a UDPSender in BIOSConfig.lua
# to send the data to the host running this script)

#CONNECTION = {
#        "type":"UDP",
#        "port":7777
#}

CONNECTION = {
        "type":"MULTICAST",
        "group":"239.255.50.10",
        "port":5010
}

CDU_COLOR = (0, 255, 0)
CHARACTER_WIDTH = 16
CHARACTER_HEIGHT = 16

KERNING = 3
LINE_SPACING = 6

SOURCE_SIZE = 16

import socket
import sys
import struct
import os
from dcsbios import ProtocolParser, StringBuffer, IntegerBuffer

if not os.path.isfile("font_A-10_CDU_small.tga"):
        print("font_A-10_CDU_small.tga not found.")
        print("press return to close")
        raw_input()
        sys.exit()

parser = ProtocolParser()

if CONNECTION["type"] == "TCP":
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((CONNECTION["host"], CONNECTION["port"]))
elif CONNECTION["type"] == "UDP":
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("0.0.0.0", CONNECTION["port"]))
elif CONNECTION["type"] == "MULTICAST":
        #s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", CONNECTION["port"]))
        group = socket.inet_aton(CONNECTION["group"])
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

s.settimeout(0)
        
import pygame
pygame.init()
main_surface = pygame.display.set_mode((24*(CHARACTER_WIDTH-KERNING),10*(CHARACTER_HEIGHT+LINE_SPACING)),pygame.FULLSCREEN)
font_img = pygame.image.load("font_A-10_CDU_small.tga")  # 128x128 pixel, 8x8 characters

pygame.mouse.set_visible(False)

def get_subimg(index):
        assert index >= 0 and index <= 63
        row = index // 8
        col = index - row*8
        img = font_img.subsurface(col*SOURCE_SIZE, row*SOURCE_SIZE, SOURCE_SIZE, SOURCE_SIZE)
        return img

pos_map = {
        chr(0xA9):0, # SYS_ACTION / "bullseye"
        chr(0xAE):1, # ROTARY / up/down arrow
        chr(0xA1):2, # DATA_ENTRY / "[]" symbol
        chr(0xBB):3, # right arrow
        chr(0xAB):4, # left arrow
        b" ":5,
        b"!":6,
        b"#":7,
        b"(":8,
        b")":9,
        b"*":10,
        b"+":11,
        b"-":12,
        b".":13,
        b"/":14,
        b"0":15,
        b"1":16,
        b"2":17,
        b"3":18,
        b"4":19,
        b"5":20,
        b"6":21,
        b"7":22,
        b"8":23,
        b"9":24,
        b":":25,
        b"=":26,
        b"?":27,
        b"A":28,
        b"B":29,
        b"C":30,
        b"D":31,
        b"E":32,
        b"F":33,
        b"G":34,
        b"H":35,
        b"I":36,
        b"J":37,
        b"K":38,
        b"L":39,
        b"M":40,
        b"N":41,
        b"O":42,
        b"P":43,
        b"Q":44,
        b"R":45,
        b"S":46,
        b"T":47,
        b"U":48,
        b"V":49,
        b"W":50,
        b"X":51,
        b"Y":52,
        b"Z":53,
        b"[":54,
        b"]":55,
        chr(0xB6):56, # filled / cursor
        chr(0xB1):57, # plus/minus
        chr(0xB0):58  # degree
        }

font = {}

for k in pos_map.keys():
        img = get_subimg(pos_map[k])
        for x in range(SOURCE_SIZE):
                for y in range(SOURCE_SIZE):
                        r,g,b,a = img.get_at((x,y))
                        if a > SOURCE_SIZE*2:
                                img.set_at((x,y), CDU_COLOR)
        img = pygame.transform.scale(img, (CHARACTER_WIDTH, CHARACTER_HEIGHT))
        font[k] = img

def finish():
        pygame.mouse.set_visible(True)
        pygame.quit()
        #quit()
        sys.exit()

def set_char(line, column, c):
        if c not in font:
                c = "?"
        main_surface.blit(font[c], ((CHARACTER_WIDTH-KERNING)*column, (CHARACTER_HEIGHT+LINE_SPACING)*line))

CDUDISPLAY_START_ADDRESS = 0x11c0
cdu_display_data = bytearray(24*10)
def update_display(address, data):
        if address < CDUDISPLAY_START_ADDRESS or address >= CDUDISPLAY_START_ADDRESS + 10*24:
                return
        offset = address - CDUDISPLAY_START_ADDRESS
        data_bytes = struct.pack("<H", data)
        cdu_display_data[offset] = data_bytes[0]
        cdu_display_data[offset+1] = data_bytes[1]
parser.write_callbacks.add(update_display)

while 1:
        pygame.event.pump()
        for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                        finish()
                if ev.type == pygame.KEYDOWN:
                        if ev.key == pygame.K_ESCAPE:
                                finish()

        main_surface.fill((0, 0, 0))

        for i in range(24*10):
                row = i // 24
                col = i - (row*24)
                set_char(row, col, chr(cdu_display_data[i]))
        
        pygame.display.flip()

        while 1:
			try:
				data = s.recv(8192)
                                if data:
                                        for c in data:
                                                parser.processByte(c)
			except:
				break;
