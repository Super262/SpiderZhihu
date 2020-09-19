from utils.zheye import zheye

z = zheye()
position = z.Recognize('zheye/a.gif')
print(position)