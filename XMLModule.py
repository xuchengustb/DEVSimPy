# -*- coding: utf-8 -*-

"""
Name: XML.py
Brief descritpion: All classes and functions linked with xml aspects
Author(s): L. Capocchi <capocchi@univ-corse.fr>
Version:  1.0
Last modified: 2012.12.18
GENERAL NOTES AND REMARKS:

GLOBAL VARIABLES AND FUNCTIONS:
"""

import os
import re
import copy
import tempfile

import xml.etree.ElementTree as ET
from xml.dom import minidom

if __name__ == '__main__':
    import __builtin__
    import sys
    ABS_HOME_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))
    __builtin__.__dict__['GUI_FLAG'] = True
    __builtin__.__dict__['DEVS_DIR_PATH_DICT'] = {'PyDEVS':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyDEVS'),
									'PyPDEVS_221':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyPDEVS','pypdevs221' ,'src'),
									'PyPDEVS':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyPDEVS','old')}
    __builtin__.__dict__['DEFAULT_DEVS_DIRNAME'] = 'PyDEVS'
    __builtin__.__dict__['HOME_PATH'] = ABS_HOME_PATH

import Container
import Components

def makeDEVSXML(label, D, filename):
	""" Make XML file from D graph of the diagram
	"""

	# build a tree structure
	root = ET.Element("CoupledModel", {'xmlns:xsi':"http://www.w3.org/2001/XMLSchema-instance", 'xmlns:xsd':"http://www.w3.org/2001/XMLSchema"})

	nom = ET.SubElement(root, "nom")
	nom.text = label

	# all of root (CoupledModel) children
	inp = ET.SubElement(root, "portsIn")
	outp = ET.SubElement(root, "portsOut")
	ioc = ET.SubElement(root, "inputCoupling")
	eoc = ET.SubElement(root, "outputCoupling")
	ic = ET.SubElement(root, "internalCoupling")
	composants = ET.SubElement(root, "composants")

	# for all models composing coupled model
	for component in D:
		# if iPort
		if isinstance(component, Container.iPort):
			# nb iport
			n = ET.SubElement(inp, "nom")
			s = ET.SubElement(n, "string")
			s.text = component.label
			# IC
			for d in D[component]:
				for comp in d:
					c = ET.SubElement(ioc, "coupling")
					s = ET.SubElement(c, "source")
					s.text = label
					ps = ET.SubElement(c, "portSource")
					ps.text = str(d[comp][0])
					dest = ET.SubElement(c, "destination")
					dest.text = comp.label
					pd = ET.SubElement(c, "portDestination")
					pd.text = str(d[comp][1])

		elif isinstance(component, Container.oPort):
			n = ET.SubElement(outp, "nom")
			s = ET.SubElement(n, "string")
			s.text = component.label
			# IC
			for d in D[component]:
				for comp in d:
					c = ET.SubElement(eoc, "coupling")
					s = ET.SubElement(c, "source")
					s.text = comp.label
					ps = ET.SubElement(c, "portSource")
					ps.text = str(d[comp][1])
					dest = ET.SubElement(c, "destination")
					dest.text = label
					pd = ET.SubElement(c, "portDestination")
					pd.text = str(d[comp][0])
		else:
			# IC
			for d in D[component]:
				for comp in filter(lambda c: isinstance(c, Container.Block),d):
					c = ET.SubElement(ic, "coupling")
					s = ET.SubElement(c, "source")
					s.text = component.label
					ps = ET.SubElement(c, "portSource")
					ps.text = str(d[comp][0])
					dest = ET.SubElement(c, "destination")
					dest.text = comp.label
					pd = ET.SubElement(c, "portDestination")
					pd.text = str(d[comp][1])
			#D
			class_name = os.path.splitext(os.path.basename(component.python_path))[0]
			model = ET.SubElement(composants, "Model", {'xsi:type':class_name})
			n = ET.SubElement(model, "nom")
			n.text = component.label
			pi = ET.SubElement(model, "portsIn")
			n = ET.SubElement(pi, "nom")
			for i in xrange(component.input):
				s = ET.SubElement(n, "string")
				# label port dont exist ! replace by the port id
				s.text = str(i)
			po = ET.SubElement(model, "portsOut")
			n = ET.SubElement(po, "nom")
			for i in xrange(component.output):
				s = ET.SubElement(n, "string")
				s.text = str(i)

	## wrap it in an ElementTree instance, and save as XML
	tree = ET.ElementTree(root)
	file = open(filename, "w")
	file.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>" + "\n")
	tree.write(file)
	file.close()

def getDiagramFromXML(xml_file="", name="", canvas=None, D={}):
	"""
	"""

	import WizardGUI

	xmldoc = minidom.parse(xml_file)

	### all item [2:] for id 0 and 1
	itemlist = xmldoc.getElementsByTagName('mxCell')[2:]

	### item corresponding to the block
	blocklist = []
	### item corresponding to the connection
	connectionlist = []
	for s in itemlist:
		if s.attributes.has_key('source') and s.attributes.has_key('target'):
			connectionlist.append(s)
		else:
			blocklist.append(s)

	#mxGraphModel = xmldoc.getElementsByTagName('mxGraphModel')[0]
	#dx = int(mxGraphModel.attributes['dx'].value)
	#dy = int(mxGraphModel.attributes['dy'].value)

	### parent of all block is canvas
	D['1'] = canvas

	### make block (atomic or coupled model)
	while(blocklist!=[]):

		s = blocklist[0]

		name = s.attributes['value'].value
		if s.attributes.has_key('style'):

			### coupled model have swimlane style or *couple{d}* in value filed
			if s.attributes['style'].value == 'swimlane' or re.match('[a-zA-Z0-9_ ]*[c|C]oupl[ed|e|é][a-zA-Z0-9_ ]*',name, re.IGNORECASE):
				attr = s.getElementsByTagName('mxGeometry')[0].attributes
				temp = tempfile.NamedTemporaryFile(suffix='.py')
				temp.write(WizardGUI.coupledCode('CoupledModel'))
				temp.seek(0)

				block = Components.BlockFactory.CreateBlock(x=int(attr['x'].value), y=int(attr['y'].value), name=name, python_file=temp.name, canvas=canvas)
				block.label = name

				parent_id = s.attributes['parent'].value
				id = str(s.attributes['id'].value)
				if parent_id == '1':
					canvas.AddShape(block)
					D[id] = block
					del blocklist[0]

				elif parent_id in D.keys():
					canvas_parent = D[parent_id]
					canvas_parent.AddShape(block)
					D[id] = block
					del blocklist[0]

				else:
					blocklist.insert(len(blocklist),blocklist.pop(0))

			elif re.match('[a-zA-Z0-9_ ]*[a|A]tomi[c|que][a-zA-Z0-9_ ]*',name, re.IGNORECASE):
				attr = s.getElementsByTagName('mxGeometry')[0].attributes
				temp = tempfile.NamedTemporaryFile(suffix='.py')
				temp.write(WizardGUI.atomicCode('AtomicModel'))
				temp.seek(0)

				block = Components.BlockFactory.CreateBlock(x=int(attr['x'].value), y=int(attr['y'].value), name=name, python_file=temp.name, canvas=canvas)
				block.label = name

				parent_id = s.attributes['parent'].value
				id = str(s.attributes['id'].value)

				if parent_id == '1':
					canvas.AddShape(block)
					D[id] = block
					del blocklist[0]

				elif parent_id in D.keys():
					canvas_parent = D[parent_id]
					canvas_parent.AddShape(block)
					D[id] = block
					del blocklist[0]

				else:
					blocklist.insert(len(blocklist),blocklist.pop(0))

		elif s.attributes.has_key('vertex'):
			if s.attributes['vertex'].value == '1' or re.match('[a-zA-Z0-9_ ]*[a|A]tomi[c|que][a-zA-Z0-9_ ]*',name, re.IGNORECASE):
				attr = s.getElementsByTagName('mxGeometry')[0].attributes
				temp = tempfile.NamedTemporaryFile(suffix='.py')
				temp.write(WizardGUI.atomicCode('AtomicModel'))
				temp.seek(0)

				block = Components.BlockFactory.CreateBlock(x=int(attr['x'].value), y=int(attr['y'].value), name=name, python_file=temp.name, canvas=canvas)
				block.label = name

				parent_id = s.attributes['parent'].value
				id = str(s.attributes['id'].value)
				if parent_id == '1':
					canvas.AddShape(block)
					D[id] = block
					del blocklist[0]

				elif parent_id in D.keys():
					canvas_parent = D[parent_id]
					canvas_parent.AddShape(block)
					D[id] = block
					del blocklist[0]

				else:
					blocklist.insert(len(blocklist),blocklist.pop(0))
		else:
			sys.stdout.write(_('Element not considered!\n'))

	### make connection
	while(connectionlist != []):
		s = connectionlist[0]

		source_id = s.attributes['target'].value
		target_id = s.attributes['source'].value
		parent_id = s.attributes['parent'].value
		#style = s.attributes['style'].value.split(';')

		source = D[source_id]
		target = D[target_id]
		c = D[parent_id]

		if source in canvas.diagram.shapes and target in canvas.diagram.shapes:
			a,b = canvas.GetNodeLists(source, target)
			if a == [] or b == []:
				a,b = canvas.GetNodeLists(target,source)
			canvas.sourceNodeList, canvas.targetNodeList = a,b
			
			if canvas.sourceNodeList != [] and canvas.targetNodeList !=[]:
				canvas.makeConnectionShape(canvas.sourceNodeList[0], canvas.targetNodeList[0])

		del connectionlist[0]

def getDiagramFromXMLSES(xmlses_file="", name="", canvas=None, D={}):
	"""
	"""

	import WizardGUI

	xmldoc = minidom.parse(xmlses_file)

	#connectionlist = xmldoc.getElementsByTagName('coupling')

	### item corresponding to the block
	blocklist = xmldoc.getElementsByTagName('treenode')

	D = {}
	for i,s in enumerate(blocklist[1:]):
		if s.hasChildNodes():
			#coupled_models.append(s)
			name = s.attributes['name'].value
			if D != {}:
				for k,v in D.items():
					if k.attributes['uid'].value == blocklist[i].attributes['parentuid'].value:
						D[k].append(s)
						break
			D[s] = []
			
		elif i+1 < len(blocklist[1:]) and not blocklist[i+2].hasChildNodes():
			for k,v in D.items():
				if k.attributes['uid'].value == s.attributes['parentuid'].value:
					D[k].append(s)
					
					break
    	else:
    		
    		for k,v in D.items():
    				if k.attributes['uid'].value == s.attributes['parentuid'].value:
					D[k].append(s)
					
					break

	already_instanciated = {}
	for coupled_model,components in D.items():
    	
		### coupled model
		name = coupled_model.attributes['name'].value
		### if coupled model is already instanciated, block is in already_instanciated
		if name not in already_instanciated:
			temp = tempfile.NamedTemporaryFile(suffix='.py', delete=False)
			temp.write(WizardGUI.coupledCode('CoupledModel'))
			temp.seek(0)

			block = Components.BlockFactory.CreateBlock(x=100, y=100, name=name, python_file=temp.name, canvas=canvas)
			block.label = name
		else:
			block = already_instanciated[name]

		for m in components:
    		
			### coupled model
			sub_name = m.attributes['name'].value
			temp = tempfile.NamedTemporaryFile(suffix='.py', delete=False)
			### if model is in the keys of D (coupled models), m i coupled model
			if m in D.keys():
				temp.write(WizardGUI.coupledCode('CoupledModel'))	
			else:
				temp.write(WizardGUI.atomicCode('AtomicModel'))	
			temp.seek(0)

			sub_block = Components.BlockFactory.CreateBlock(x=100, y=100, name=sub_name, python_file=temp.name, canvas=canvas)
			sub_block.label = sub_name
			
			### if m is a coupled model, we store the associated block (sub_name = Numi8)
			if m in D.keys():already_instanciated[sub_name] = sub_block

			block.AddShape(sub_block)

		if name not in already_instanciated:
			canvas.AddShape(block)
		
	### TODO : coupling

	return True

	### parent of all block is canvas
	D['1'] = canvas

	### make block (atomic or coupled model)
	while(blocklist!=[]):

		s = blocklist[0]

		name = s.attributes['value'].value
		if s.attributes.has_key('style'):

			### coupled model have swimlane style or *couple{d}* in value filed
			if s.attributes['style'].value == 'swimlane' or re.match('[a-zA-Z0-9_ ]*[c|C]oupl[ed|e|é][a-zA-Z0-9_ ]*',name, re.IGNORECASE):
				attr = s.getElementsByTagName('mxGeometry')[0].attributes
				temp = tempfile.NamedTemporaryFile(suffix='.py')
				temp.write(WizardGUI.coupledCode('CoupledModel'))
				temp.seek(0)

				block = Components.BlockFactory.CreateBlock(x=int(attr['x'].value), y=int(attr['y'].value), name=name, python_file=temp.name, canvas=canvas)
				block.label = name

				parent_id = s.attributes['parent'].value
				id = str(s.attributes['id'].value)
				if parent_id == '1':
					canvas.AddShape(block)
					D[id] = block
					del blocklist[0]

				elif parent_id in D.keys():
					canvas_parent = D[parent_id]
					canvas_parent.AddShape(block)
					D[id] = block
					del blocklist[0]

				else:
					blocklist.insert(len(blocklist),blocklist.pop(0))

			elif re.match('[a-zA-Z0-9_ ]*[a|A]tomi[c|que][a-zA-Z0-9_ ]*',name, re.IGNORECASE):
				attr = s.getElementsByTagName('mxGeometry')[0].attributes
				temp = tempfile.NamedTemporaryFile(suffix='.py')
				temp.write(WizardGUI.atomicCode('AtomicModel'))
				temp.seek(0)

				block = Components.BlockFactory.CreateBlock(x=int(attr['x'].value), y=int(attr['y'].value), name=name, python_file=temp.name, canvas=canvas)
				block.label = name

				parent_id = s.attributes['parent'].value
				id = str(s.attributes['id'].value)

				if parent_id == '1':
					canvas.AddShape(block)
					D[id] = block
					del blocklist[0]

				elif parent_id in D.keys():
					canvas_parent = D[parent_id]
					canvas_parent.AddShape(block)
					D[id] = block
					del blocklist[0]

				else:
					blocklist.insert(len(blocklist),blocklist.pop(0))

		elif s.attributes.has_key('vertex'):
			if s.attributes['vertex'].value == '1' or re.match('[a-zA-Z0-9_ ]*[a|A]tomi[c|que][a-zA-Z0-9_ ]*',name, re.IGNORECASE):
				attr = s.getElementsByTagName('mxGeometry')[0].attributes
				temp = tempfile.NamedTemporaryFile(suffix='.py')
				temp.write(WizardGUI.atomicCode('AtomicModel'))
				temp.seek(0)

				block = Components.BlockFactory.CreateBlock(x=int(attr['x'].value), y=int(attr['y'].value), name=name, python_file=temp.name, canvas=canvas)
				block.label = name

				parent_id = s.attributes['parent'].value
				id = str(s.attributes['id'].value)
				if parent_id == '1':
					canvas.AddShape(block)
					D[id] = block
					del blocklist[0]

				elif parent_id in D.keys():
					canvas_parent = D[parent_id]
					canvas_parent.AddShape(block)
					D[id] = block
					del blocklist[0]

				else:
					blocklist.insert(len(blocklist),blocklist.pop(0))
		else:
			sys.stdout.write(_('Element not considered!\n'))

	### make connection
	while(connectionlist != []):
		s = connectionlist[0]

		source_id = s.attributes['target'].value
		target_id = s.attributes['source'].value
		parent_id = s.attributes['parent'].value
		#style = s.attributes['style'].value.split(';')

		source = D[source_id]
		target = D[target_id]
		c = D[parent_id]

		if source in canvas.diagram.shapes and target in canvas.diagram.shapes:
			a,b = canvas.GetNodeLists(source, target)
			if a == [] or b == []:
				a,b = canvas.GetNodeLists(target,source)
			canvas.sourceNodeList, canvas.targetNodeList = a,b
			
			if canvas.sourceNodeList != [] and canvas.targetNodeList !=[]:
				canvas.makeConnectionShape(canvas.sourceNodeList[0], canvas.targetNodeList[0])

		del connectionlist[0]

if __name__ == '__main__':
	import wx

	### ------------------------------------------------------------
	class TestApp(wx.App):
		""" Testing application
		"""

		def OnInit(self):

			import DetachedFrame
			import __builtin__
			import gettext
			from DomainInterface.DomainStructure import DomainStructure
			from DomainInterface.DomainBehavior import DomainBehavior

			__builtin__.__dict__['ICON_PATH']='icons'
			__builtin__.__dict__['ICON_PATH_16_16']=os.path.join(ICON_PATH,'16x16')
			__builtin__.__dict__['NB_HISTORY_UNDO']= 5
			__builtin__.__dict__['DOMAIN_PATH']='Domain'
			
			__builtin__.__dict__['FONT_SIZE']=12
			__builtin__.__dict__['_'] = gettext.gettext
			__builtin__.__dict__['LOCAL_EDITOR'] = False

			diagram = Container.Diagram()
			
			self.frame = DetachedFrame.DetachedFrame(None, -1, "Test", diagram)
			newPage = Container.ShapeCanvas(self.frame, wx.NewId(), name='Test')
			newPage.SetDiagram(diagram)

			#getDiagramFromXML("Diagram.xml", canvas=newPage)
			path = os.path.join(os.path.expanduser("~"),'Downloads','example.xmlsestree')
			getDiagramFromXMLSES(path, canvas=newPage)
			#diagram.SetParent(newPage)

			self.frame.Show()

			return True

		def OnQuit(self, event):
			self.Close()

	app = TestApp(0)
	app.MainLoop()