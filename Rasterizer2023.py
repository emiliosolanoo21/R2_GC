from gl import Renderer
import shaders
width = 2048
height = 2048

rend = Renderer(width, height)
rend.vertexShader = shaders.vertexShader
rend.fragmentShader = shaders.fragmentShader

rend.glLoadModel(filename = "model.obj", texName = "model.bmp", translate=(1530, 500, 0), rotate=(3, 0, -1), scale=(300, 300, 300))
rend.glLoadModel(filename = "model.obj", texName = "model.bmp", translate=(500, 1530, 0), rotate=(-2, 0, -1), scale=(300, 300, 300))
rend.glLoadModel(filename = "model.obj", texName = "model.bmp", translate=(500, 500, 0), rotate=(0, 4, -1.32), scale=(300, 300, 300))
rend.glLoadModel(filename = "model.obj", texName = "model.bmp", translate=(1530, 1530, 0), rotate=(-1.75, 0, -1.5), scale=(300, 300, 300))

rend.glRender()

#Nombre del framebuffer creado y guardado.
rend.glFinish("result.bmp")