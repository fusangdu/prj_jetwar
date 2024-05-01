import time
from time import sleep
import threading
import random #官方模块
import pygame #第三方模块
#应用程序模块

######################剩余待做###########################
#重新开始弹窗
#炸弹；life
#被攻击时换图
#暂停和继续


#屏幕大小的常量 
SCREEN_RECT=pygame.Rect(0,0,480,700)
#刷新的帧率
FRAME_PER_SEC=60
#创建敌机的定时器常量
CREATE_ENEMY_EVENT=pygame.USEREVENT
#创建超级敌机的定时器常量
CREATE_SUPERENEMY_EVENT=pygame.USEREVENT+1

#击毁敌机数量统计
ENEMYCOUNT=0
#boss出场次数控制
BOSSCOUNT=1
#boss二阶段水平移动控制
HORIZONTALTURN=-1
#暴走音乐播放次数控制
MUSICCOUNT=1


class GameSprite(pygame.sprite.Sprite):
    """GameSprite类"""
    def __init__(self,image_name,speed=1):
        #调用父类初始化方法
        super().__init__()
        #定义对象的属性：图片和初始垂直速度
        self.image=pygame.image.load(image_name)
        self.rect = self.image.get_rect()
        self.speed=speed
    

class Background(GameSprite):
    """游戏背景"""
    def __init__(self,is_alt=False):
        super().__init__("./prj_jetwar/images/background.png")   #这里写死了图片地址因为只有一个背景，所以子类的__init__方法里面就不需要传这个参了
        
        #通过is_alt分别创建两个上下连接的背景
        if is_alt:
            self.rect.y=-self.rect.height
    
    def update(self):
        #背景以速度滚动
        self.rect.y += self.speed  
        #2.判断是否移除屏幕，如果移出屏幕，将图像设置到屏幕上方
        if self.rect.y >= SCREEN_RECT.height:
            self.rect.y = -self.rect.height
        


class Enemy(GameSprite):
    """小敌机"""
    def __init__(self,screen,imagepath="./prj_jetwar/images/enemy1.png",soundpath="./prj_jetwar/musics/explosion2.mp3",destroyimages=["./prj_jetwar/images/enemy1_down1.png","./prj_jetwar/images/enemy1_down2.png","./prj_jetwar/images/enemy1_down3.png","./prj_jetwar/images/enemy1_down4.png"]):
        #调用父类方法，创见敌机，同时指定敌机图片
        super().__init__(imagepath)

        #覆写敌机初始垂直随机速度
        self.speed=random.randint(1,2)+ random.gauss(0.3,0.3)

        #敌机水平恒定速度
        self.xspeed=random.randint(-1,1)
        
        #敌机初始随机位置
        self.rect.bottom=0
        max_x=SCREEN_RECT.width-self.rect.width    #只是顺序执行__init__所以可以这么写
        self.rect.x=random.randint(0,max_x)        #水平随机位置出现

        #爆炸音效
        pygame.mixer.init()
        self.explosound=pygame.mixer.Sound(soundpath)
        #爆炸图片
        self.destroyimages=destroyimages

        #传入screen，用于把特效画在背景上。screen好像不能设置为全局变量，因为screen是游戏大类初始化时才创建
        self.screen=screen

    def update(self):
        #垂直方向上运动
        self.rect.y += self.speed
        #水平方向上运动
        self.rect.x += self.xspeed+random.gauss(0,2)
        #飞出屏幕需要从精灵组删除释放内存
        if self.rect.y>=SCREEN_RECT.height:
            self.silentkill() #从所有组中删除。  ##我发现如果要让Enemy的实例调用其在程序运行过程中所归属的Group实例，需要在创建Enemy实例时把Group实例传参进来初始化。在plane_sprites中定义敌机组作为全局变量也可以，但是不太符合面向对象的程序设计思路
             
    def kill(self):
        #播放爆炸声音
        self.explosound.play()
        #创建特效
        explosion=Explosion(self.rect.topleft,self.screen,*self.destroyimages,p=3)
        
        #释放特效，需要多线程，否则影响主程序会卡顿
        m1=myThread(explosion)
        m1.start()

        super().kill()

        #消灭敌机数量统计，用来触发boss
        global ENEMYCOUNT
        ENEMYCOUNT +=1

    #飞出屏幕的无声移除内存
    def silentkill(self):
        super().kill()



class SuperEnemy(Enemy):
    """中型敌机"""
    def __init__(self,screen,enemy_bullets_group):
        #继承小敌机
        super().__init__(screen,imagepath="./prj_jetwar/images/enemy2.png",soundpath="./prj_jetwar/musics/explosion3.mp3",destroyimages=["./prj_jetwar/images/enemy2_down1.png","./prj_jetwar/images/enemy2_down2.png","./prj_jetwar/images/enemy2_down3.png","./prj_jetwar/images/enemy2_down4.png"])
        
        #调用定义在主游戏类里的敌机子弹组
        self.enemy_bullets_group=enemy_bullets_group
        
        #加载射击、被击中、音效
        pygame.mixer.init()
        self.gunsound=pygame.mixer.Sound("./prj_jetwar/musics/laser1.mp3")
        self.hitsound=pygame.mixer.Sound("./prj_jetwar/musics/metalhit3.mp3")
        #记录实例创建时间，用来控制子弹发射频率
        self.create_time=time.time()
        #生命值
        self.life=18


    def fire(self):
        #创建bullet，子弹类传入图片和速度
        bullet=Bullet("./prj_jetwar/images/bullet2.png",speed=3)
        #设置子弹初始位置
        bullet.rect.centerx = self.rect.centerx
        bullet.rect.top=self.rect.bottom
        #把子弹添加到组
        self.enemy_bullets_group.add(bullet)
        #播放枪声
        self.gunsound.play()
    
    def update(self):
        super().update()
        #定时发射子弹，因为不是组内所有中型敌机同时发射子弹，所以要定义到跟实例创造时间相关的方法里
        if time.time()-self.create_time>2:
            self.fire()
            self.create_time+=4
    
    def kill(self):
        #播放被击打音效
        self.hitsound.play() 
        #扣血和击杀
        self.life -= 3
        if self.life <=0:
            super().kill()


#考虑到Boss类有很多要重写的地方，干脆不从中型敌机、小型敌机开始继承
class Boss(GameSprite):
    """大BOSS"""
    def __init__(self,screen,bullets_group,imagepath=["./prj_jetwar/images/enemy3_n1.png","./prj_jetwar/images/enemy3_n2.png"],soundpath="./prj_jetwar/musics/loudexplosion.mp3",hitsound="./prj_jetwar/musics/metalhit3.mp3",gunsound="./prj_jetwar/musics/laser1.mp3",destroyimages=["./prj_jetwar/images/enemy3_down1.png","./prj_jetwar/images/enemy3_down2.png","./prj_jetwar/images/enemy3_down3.png","./prj_jetwar/images/enemy3_down4.png","./prj_jetwar/images/enemy3_down5.png","./prj_jetwar/images/enemy3_down6.png"]):
        #调用父类方法，创见敌机，同时指定敌机初始图片
        super().__init__(imagepath[0])
        #存储BOSS两张图片，用于生成动态效果
        self.imagecollect=imagepath
        #自毁图片列表
        self.destroyimages=destroyimages

        #敌机初始垂直速度
        self.speed=0.7
        #水平速度
        self.speedh=0
        
        #敌机初始随机位置
        self.rect.bottom=0
        self.rect.centerx=SCREEN_RECT.centerx

        #5.爆炸、被击中、射击音效
        pygame.mixer.init()
        self.explosound=pygame.mixer.Sound(soundpath)
        self.hitsound=pygame.mixer.Sound(hitsound)
        self.gunsound=pygame.mixer.Sound(gunsound)
        
        #血量
        self.life=150
        
        #子弹组
        self.bullets_group=bullets_group
        #创建时间，用于控制自动发射子弹
        self.create_time=time.time()
        
        #传入screen，用于把特效画在背景上。screen好像不能设置为全局变量，因为screen是游戏大类初始化时才创建
        self.screen=screen
    
    def update(self):
        #换装动态效果
        imagechange=random.randint(0,1)
        self.image=pygame.image.load(self.imagecollect[imagechange])

        #垂直方向下运动直到固定位置
        self.rect.y += self.speed
        #水平方向控制
        self.rect.x += self.speedh
        #垂直移动到固定位置停止
        if self.rect.y>=10:
            self.rect.y=10

        #发射子弹的时间控制
        if time.time()-self.create_time>1:
            self.fire()
            self.create_time+=4

        #二阶段暴走判断，血量低于200
        if self.life <= 100:
            global HORIZONTALTURN
            self.speedh=5*HORIZONTALTURN
            if self.rect.x<=0:
                HORIZONTALTURN=1
            elif self.rect.x>=310:
                HORIZONTALTURN=-1 

            #控制播放一次暴走音乐
            global MUSICCOUNT
            if MUSICCOUNT==1:
                MUSICCOUNT+=1
                pygame.mixer.init()
                pygame.mixer.music.load("./prj_jetwar/musics/jinitaimei.mp3")
                pygame.mixer.music.play(1)

             
    def kill(self):
        #播放被击打音效
        self.hitsound.play() 
        #扣血
        self.life -= 3
        #死亡
        if self.life <=0:
            #播放爆炸音效
            self.explosound.play()
            #创建爆炸特效
            explosion=Explosion(self.rect.topleft,self.screen,*self.destroyimages,p=3)
            #释放爆炸特效，不做成多线程，因为boss死了游戏结束
            explosion.update()
            #移除内存
            super().kill()
            
            global ENEMYCOUNT
            ENEMYCOUNT +=1

    def fire(self):
        for i in (-1,0,1):
            #创建bullet
            bullet=Bullet("./prj_jetwar/images/bullet2.png",speed=3)
            #设置子弹初始位置，水平发射三枚
            bullet.rect.x=self.rect.centerx-15 * i
            bullet.rect.top = self.rect.bottom
            #把子弹添加到组
            self.bullets_group.add(bullet)
            #播放射击音效
            self.gunsound.play() 
            


class Hero(GameSprite):
    """英雄"""
    def __init__(self,screen):
        super().__init__("./prj_jetwar/images/me2.png",0)

        #初始位置
        self.rect.centerx=SCREEN_RECT.centerx
        self.rect.bottom=SCREEN_RECT.bottom

        #因为英雄是在游戏类初始化时作为其属性被创建，所以即使英雄子弹组作为英雄的属性被创建，游戏类实例也可以直接调用这个子弹类（是其属性的属性）
        self.bullets=pygame.sprite.Group() #创建英雄发射的子弹类
        
        #加载射击、爆炸、被击中音效
        pygame.mixer.init()
        self.gunsound=pygame.mixer.Sound("./prj_jetwar/musics/machinegun2.mp3")
        self.explosound=pygame.mixer.Sound("./prj_jetwar/musics/explosion2.mp3")
        self.hitsound=pygame.mixer.Sound("./prj_jetwar/musics/metalhit3.mp3")
        
        #生命值
        self.life=3

        self.screen=screen

    def update(self):
        #水平方向移动
        self.rect.x += self.speed #speed属性是程序运行过程中通过监听到用户的按键而被赋予Hero的
        #不移出边界
        if self.rect.right> SCREEN_RECT.right:
            self.rect.right=SCREEN_RECT.right
        elif self.rect.x<0:
            self.rect.x=0
        
        #垂直方向移动
        self.rect.y += self.speedh #speedh属性是程序运行过程中赋予Hero的,且并没有被初始化过
        #不移出边界
        if self.rect.y<0:
            self.rect.y=0
        elif self.rect.bottom>SCREEN_RECT.bottom:
            self.rect.bottom=SCREEN_RECT.bottom
        
    def fire(self):
        #一次发射三枚垂直子弹
        for i in (0,1,2):
            #创建bullet
            bullet=Bullet()
            #设置子弹初始位置
            bullet.rect.centerx = self.rect.centerx
            bullet.rect.bottom=self.rect.y-20 * i
            #把子弹添加到组
            self.bullets.add(bullet)
            #播放音效
            self.gunsound.play()

    def kill(self):
        #播放被击打音效
        self.hitsound.play() 
        #扣血
        self.life -= 1
        #被击杀判断
        if self.life <=0:
            #播放爆炸音效
            self.explosound.play()
            #创建特效
            explosion=Explosion(self.rect.topleft,self.screen,"./prj_jetwar/images/me_destroy_1.png","./prj_jetwar/images/me_destroy_2.png","./prj_jetwar/images/me_destroy_3.png","./prj_jetwar/images/me_destroy_4.png")
            #释放特效
            explosion.update()
            super().kill()
            sleep(1) #英雄死亡暂停一秒


           

                

class Bullet(GameSprite):
    """敌我所有子弹"""
    def __init__(self,bulletpath="./prj_jetwar/images/bullet1.png",speed=-3):
        super().__init__(bulletpath,speed=speed)

    def update(self):
        #子弹垂直移动更新
        self.rect.y += self.speed
        #子弹飞出上下边界需被移出内存
        if self.rect.bottom<0:
            self.kill()
        elif self.rect.bottom>700:
            self.kill()

    def __del__(self):
        print("子弹被删除")


class Explosion(pygame.sprite.Sprite):
    """所有爆炸的动画特效"""
    def __init__(self,position,screen,*pathlist,p=3):
        super().__init__()
        #动态效果图片，张数可不同
        self.image=[
            pygame.image.load(i) for i in pathlist
        ]
        #根据张数不同需要设置不同的p值
        self.p=p

        #爆炸位置的设置
        self.rect=self.image[0].get_rect()
        self.rect.topleft=position
        #因为screen是在游戏大类初始化时被定义，所以不能做成全局变量。需要被传入这个参数
        self.screen=screen

    #因为是具体的对象分别在kill时产生爆炸类实例，并对实例调用update方法释放爆炸的动态效果。所以没有考虑把爆炸实例纳入组来管理update
    def update(self):
        #播放爆炸动态效果
        for i in range(self.p):
            self.screen.blit(self.image[i%self.p],self.rect.topleft)
            pygame.display.flip() #切换完图片，更新屏幕
            sleep(0.1)
        #最后一张不写进循环是考虑到最后的烟雾可以区分设置停留
        self.screen.blit(self.image[-1],self.rect.topleft)
        pygame.display.flip()#切换完图片，更新屏幕
        sleep(0.1)

        #播放结束删除特效对象
        self.kill() 
    
        print("特效结束")



#多线程的类方法调用
class myThread(threading.Thread):
    def __init__(self,instance):
        #父类初始化
        threading.Thread.__init__(self)
        #把实例放在这里
        self.instance=instance
    #线程start即是调用这个run方法
    def run(self):
        #给爆炸类的update方法用的
        self.instance.update()





























