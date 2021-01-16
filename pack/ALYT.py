# -*- coding:utf-8 -*-
from util.rawutil import TypeWriter
from util.filesystem import *
from util.utils import ClsFunc
from util import error
from .SARC import packSARC


class packALYT (ClsFunc, TypeWriter):
	def main(self, filenames, outname, endian, verbose, opts={}):
		self.byteorder = endian
		self.verbose = verbose
		self.getmeta(filenames)
		self.repack_ALYT()
		final = self.repack_all()
		basedir()
		bwrite(final, outname)
	
	def getmeta(self, filenames):
		self.files = [name for name in filenames if os.path.basename(os.path.dirname(name)) != '_alyt_']
		if len(self.files) == len(filenames):
			#no _alyt_ folder, aborting
			error.NeededDataNotFoundError('No _alyt_ folder in the specified directory')
		self.alyt_folder = [os.path.dirname(name) for name in filenames if os.path.basename(os.path.dirname(name)) == '_alyt_'][0]  # horrible hack
		self.basedirectory = os.path.dirname(self.alyt_folder)
		metadir = self.alyt_folder + os.path.sep
		try:
			file = metadir + 'LTBL.bin'
			self.ltbl = bread(file)
			file = metadir + 'LMTL.bin'
			self.lmtl = bread(file)
			file = metadir + 'LFNL.bin'
			self.lfnl = bread(file)
			file = metadir + 'nametable.txt'
			self.nametable = [[el] for el in bread(file).splitlines()]
			file = metadir + 'symtable.txt'
			self.symtable = [[el] for el in bread(file).splitlines()]
		except FileNotFoundError:
			#That's why a temporary file var is used
			error.NeededDataNotFoundError('No %s file found in the specified directory' % file)
		
	def repack_ALYT(self):
		self.ltbloffset = 0x28
		self.alyt = bytearray(0x28)
		self.alyt += self.ltbl
		self.lmtloffset = len(self.alyt)
		self.alyt += self.lmtl
		self.lfnloffset = len(self.alyt)
		self.alyt += self.lfnl
		self.alyt += (0x80 - (len(self.alyt) % 0x80)) * b'\x00'
		self.dataoffset = len(self.alyt)
		self.alyt += self.pack('I/0[n64a]', len(self.nametable), self.nametable)
		self.alyt += self.pack('I/0[n32a]', len(self.symtable), self.symtable)
		self.alyt += (0x80 - (len(self.alyt) % 0x80)) * b'\x00'
	
	def repack_all(self):
		if self.verbose:
			print('Packing SARC')
		sarc, sarc_endpad = packSARC(self.files, None, self.byteorder, self.verbose, embedded=True, basedirectory=self.basedirectory)
		if self.verbose:
			print('Packing ALYT')
		final = self.alyt + sarc
		hdr = self.pack('4s9I', 'ALYT', 0x00040002, self.ltbloffset, len(self.ltbl), self.lmtloffset, len(self.lmtl), self.lfnloffset, len(self.lfnl), self.dataoffset, len(final) - sarc_endpad - self.dataoffset)
		final[0:0x28] = hdr
		return final
