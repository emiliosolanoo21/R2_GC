'''
Libreria para simular las variables como
si estuvieran escritas en C.
'''
import struct
from collections import namedtuple
from obj import Obj
from operations import MxM, barycentricCoords
from texture import Texture
from math import sin, cos


V2 = namedtuple('Point1', ['x', 'y'])
V3 = namedtuple('Point2', ['x', 'y', 'z'])
triangles = 2

def char(c):
    #1 byte
    return struct.pack('=c', c.encode('ascii'))

def word(w):
    #2 bytes
    return struct.pack('=h', w)

def dword(d):
    #4 bytes
    return struct.pack('=l', d)

def color(r, g, b):
    '''
    Lo que regresa esto es un pixel y,
    la cantidad de rojo, verde y azul
    que tendrá.
    '''
    return bytes([int(b * 255),
                  int(g * 255),
                  int(r * 255)])

class Model(object):
    def __init__(self, filename, translate = (0, 0, 0), rotate = (0, 0, 0), scale = (1, 1, 1)):
        model = Obj(filename)

        self.vertices = model.vertices
        self.textcoords = model.textcoords
        self.normals = model.normals
        self.faces = model.faces
        
        self.translate = translate
        self.rotate = rotate
        self.scale = scale
    
    def loadTexture(self, texName):
        self.texture = Texture(texName)   

class Renderer(object):
    #Constructor
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
        self.glClearColor(0.23,0.568,0.245)
        self.glClear()

        self.glColor(1, 1, 1)

        self.vertexShader = None
        self.fragmentShader = None
        self.primitiveType = triangles
        self.vertexBuffer = []

        self.activeTexture = None

        self.objects = []
        
    #Definir color del fondo
    def glClearColor(self, r, g, b):
        self.clearcolor = color(r, g, b)
    
    def glClear(self):
        self.pixels = [[self.clearcolor for y in range(self.height)]
                        for x in range(self.width)]
        
        self.zbuffer = [[float('inf') for y in range(self.height)]
                        for x in range (self.width)] 
    
    def glColor(self, r, g, b):
        self.currColor = color(r, g, b)
        
    def glPoint(self, x, y, clr = None):
        if(0 <= x < self.width) and (0 <= y < self.height):
            self.pixels[x][y] = clr or self.currColor
    
    def glLine(self, v0, v1, clr = None):
        x0 = int(v0[0])
        x1 = int(v1[0])
        y0 = int(v0[1])
        y1 = int(v1[1])

        if (x0 == x1 and y0 == y1):
            self.glPoint(x0, y0)
            return

        dy = abs(y1 - y0)
        dx = abs(x1 - x0)

        steep = dy > dx

        if steep:
            x0, y0 = y0, x0
            x1, y1 = y1, x1

        if x0 > x1:
            x0, x1 = x1, x0
            y0, y1 = y1, y0
        
        dy = abs(y1 - y0)
        dx = abs(x1 - x0)

        m = dy / dx
        y = y0

        offset = 0
        limit = 0.5

        for x in range(x0, x1 + 1):
            if steep:
                self.glPoint(y, x, clr or self.currColor)
            else:
                self.glPoint(x, y, clr or self.currColor)
            offset += m

            if (offset >= limit):
                if (y0 < y1):
                    y += 1
                else:
                    y -= 1
                limit += 1


    def glTriangle(self, v0, v1, v2, clr = None):

        def paintFlatBottomTri(v0, v1, v2):
            try:
                m1 = (v1[0] - v0[0]) / (v1[1] - v0[1])
                m2 = (v2[0] - v0[0]) / (v2[1] - v0[1])
            except:
                pass
            else:
                x0, x1 = v1[0], v2[0]

                for y in range(v1[1], v0[1]):
                    self.glLine((x0, y), (x1, y))
                    x0 += m1
                    x1 += m2
        
        def paintFlatTopTri(v0, v1, v2):
            try:
                m1 = (v2[0] - v0[0]) / (v2[1] - v0[1])
                m2 = (v2[0] - v1[0]) / (v2[1] - v1[1])
            except:
                pass
            else:
                x0, x1 = v0[0], v1[0]

                for y in range(v0[1], v2[1], -1):
                    self.glLine((x0, y), (x1, y))
                    x0 -= m1
                    x1 -= m2

        if (v0[1] < v1[1]):
            v0, v1, = v1, v0
        if (v0[1] < v2[1]):
            v0, v2 = v2, v0
        if (v1[1] < v2[1]):
            v1, v2 = v2, v1
        
        if (v1[1] == v2[1]):
            paintFlatBottomTri(v0, v1, v2)
        elif (v0[1] == v1[1]):
            paintFlatTopTri(v0, v1, v2)
        else:
            v3 = [v0[0] + ((v1[1] - v0[1]) / (v2[1] - v0[1])) * (v2[0] - v0[0]), v1[1]]
            paintFlatBottomTri(v0, v1, v3)
            paintFlatTopTri(v1, v3, v2)

        self.glLine(v0, v1, clr or self.currColor)
        self.glLine(v1, v2, clr or self.currColor)
        self.glLine(v2, v0, clr or self.currColor)

    def glTriangleBC(self, A, B, C, vta, vtb, vtc):
        minX = round(min(A[0], B[0], C[0]))
        minY = round(min(A[1], B[1], C[1]))
        maxX = round(max(A[0], B[0], C[0]))
        maxY = round(max(A[1], B[1], C[1]))

        for x in range(minX, maxX + 1):
            for y in range(minY, maxY + 1):
                P = [x, y]
                bcoords = barycentricCoords(A, B, C, P)
                try:
                    u, v, w = bcoords

                    z = u * A[2] + v * B[2] + w * C[2]

                    if(z < self.zbuffer[x][y]):
                        self.zbuffer[x][y] = z

                        uvs = [u * vta[0] + v * vtb[0] + w * vtc[0],
                                u * vta[1] + v * vtb[1] + w * vtc[1],
                                u * vta[2] + v * vtb[2] + w * vtc[2]]
                        
                        if (self.fragmentShader != None):
                            colorP = self.fragmentShader(textcoords = uvs, texture = self.activeTexture)
                            self.glPoint(x, y, color(colorP[0], colorP[1], colorP[2]))
                        else:
                            self.glPoint(x, y, self.currColor)
                except:
                    pass
        
    def glAddVertices(self, verts):
        for v in verts:
            self.vertexBuffer.append(v)

    def glPrimitiveAssembly(self, tVerts, ttextcoords):
        primitives = []

        if (self.primitiveType == triangles):
            for i in range(0, len(tVerts), 3):
                triangle = []
                triangle.append(tVerts[i])
                triangle.append(tVerts[i + 1])
                triangle.append(tVerts[i + 2])

                triangle.append(ttextcoords[i])
                triangle.append(ttextcoords[i + 1])
                triangle.append(ttextcoords[i + 2])

                primitives.append(triangle)
            
        return primitives
    
    def glLoadModel(self, filename, texName, translate = (0, 0, 0), rotate = (0, 0, 0), scale = (1, 1, 1)):
        model = Model(filename, translate, rotate, scale)
        model.loadTexture(texName)

        self.objects.append(model)
    
    def glRender(self):
        tVerts = []
        tCoords = []

        for model in self.objects:
            self.activeTexture = model.texture
            mMatrix = self.glModelMatrix(model.translate, model.rotate, model.scale)
            

            for face in model.faces:
                vertCount = len(face)
                
                v0 = model.vertices[face[0][0] - 1]
                v1 = model.vertices[face[1][0] - 1]
                v2 = model.vertices[face[2][0] - 1]

                if vertCount == 4:
                    v3 = model.vertices[face[3][0] - 1]
                
                if self.vertexShader:
                    v0 = self.vertexShader(v0, modelMatrix = mMatrix)
                    v1 = self.vertexShader(v1, modelMatrix = mMatrix)
                    v2 = self.vertexShader(v2, modelMatrix = mMatrix)
                    if vertCount == 4:
                        v3 = self.vertexShader(v3, modelMatrix = mMatrix)
                
                tVerts.append(v0)
                tVerts.append(v1)
                tVerts.append(v2)
                if vertCount == 4:
                    tVerts.append(v0)
                    tVerts.append(v2)
                    tVerts.append(v3)

                vt0 = model.textcoords[face[0][1] - 1]
                vt1 = model.textcoords[face[1][1] - 1]
                vt2 = model.textcoords[face[2][1] - 1]
                if vertCount == 4:
                    vt3 = model.textcoords[face[3][1] - 1]
                
                tCoords.append(vt0)
                tCoords.append(vt1)
                tCoords.append(vt2)
                if vertCount == 4:
                    tCoords.append(vt0)
                    tCoords.append(vt2)
                    tCoords.append(vt3)
        
        primitives = self.glPrimitiveAssembly(tVerts, tCoords)

        for prim in primitives:
            if (self.primitiveType == triangles):
                    self.glTriangleBC(prim[0], prim[1], prim[2], prim[3], prim[4], prim[5])

    def rotationMatCalc(self, t, w, a):
        rx = [[1, 0, 0, 0],
            [0, cos(t), -sin(t), 0],
            [0, sin(t), cos(t), 0],
            [0, 0, 0, 1]]

        ry = [[cos(w), 0, sin(w), 0],
            [0, 1, 0, 0],
            [-sin(w), 0, cos(w), 0],
            [0, 0, 0, 1]]
        
        rz = [[cos(a), -sin(a), 0, 0],
            [sin(a), cos(a), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]]

        temp = MxM(rx, ry)

        return MxM(temp, rz)

    def glModelMatrix(self, translate = (0, 0, 0), rotation = (0, 0, 0), scale = (1, 1, 1)):
        translation = [[1, 0, 0, translate[0]],
                        [0, 1, 0, translate[1]],
                        [0, 0, 1, translate[2]],
                        [0, 0, 0, 1]]

        scaleMat = [[scale[0], 0, 0, 0],
                    [0, scale[1], 0, 0],
                    [0, 0, scale[2], 0],
                    [0, 0, 0, 1]]

        rotationMat = self.rotationMatCalc(rotation[0], rotation[1], rotation[2])

        temp = MxM(translation, rotationMat)

        return MxM(temp, scaleMat)
    
    def glFinish(self, filename):
        with open(filename, "wb") as file:
        #Formato de un archivo bmp:
            #Header
            file.write(char("B"))
            file.write(char("M"))
            file.write(dword(14 + 40 + (self.width * self.height) * 3))
            file.write(dword(0))
            file.write(dword(14 + 40))
            
            #InfoHeader
            file.write(dword(40))
            file.write(dword(self.width))
            file.write(dword(self.height))
            file.write(word(1))
            file.write(word(24))
            file.write(dword(0))
            file.write(dword((self.width * self.height) * 3))
            file.write(dword(0))
            file.write(dword(0))
            file.write(dword(0))
            file.write(dword(0))
            
            #ColorTable
            for y in range(self.height):
                for x in range(self.width):
                    file.write(self.pixels[x][y])
    