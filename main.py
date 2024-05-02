#!/usr/bin/python
# -*- coding: utf-8 -*-
import pygame
from plane_sprites import *
# from plane_scrites import PlaneGame


class PlaneGame:
    """飞机大战主游戏类"""
    
    def __init__(self):
        #创建游戏窗口
        self.screen=pygame.display.set_mode(SCREEN_RECT.size)
        #创建游戏时钟，控制帧率
        self.clock=pygame.time.Clock()
        #调用私有方法，创建敌机和敌机组、背景背景组
        self.__create_sprites()
        
        #设置定时器事件-创建敌机
        pygame.time.set_timer(CREATE_ENEMY_EVENT,1000)
        #设置定时器事件-创建超级敌机
        pygame.time.set_timer(CREATE_SUPERENEMY_EVENT,4000)

        #加载背景音乐，无限循环
        pygame.mixer.init()
        pygame.mixer.music.load("./musics/Brinstar.mp3")
        pygame.mixer.music.play(-1)

    def __create_sprites(self):
        #创建背景精灵和背景精灵组
        bg1 = Background()
        bg2=  Background(True)
        self.back_group=pygame.sprite.Group(bg1,bg2)

        #创建敌机的精灵组，敌机本身是在循环中不断创建
        self.enemy_group=pygame.sprite.Group()

        #创建敌人子弹组
        self.enemy_bullets=pygame.sprite.Group()

        #创建英雄和英雄组
        self.hero=Hero(self.screen) #需要把英雄定义为属性，才能在其他方法中使用英雄对象
        self.hero_group=pygame.sprite.Group(self.hero)



    def start_game(self):
        #游戏大循环
        while True:
            #设置刷新帧率
            self.clock.tick(FRAME_PER_SEC)
            #事件监听
            self.__event_handler()
            #碰撞检测
            self.__check_collide()
            #检查boss是否该出场
            self.__check_boss()
            #更新绘制精灵组
            self.__update_sprites()
            #更新显示
            pygame.display.update()

            #游戏结束的判断
            #英雄死亡
            if not self.hero.alive():
                sleep(2)
                PlaneGame.__game_over()
            #BOSS死亡
            try:
                if not self.boss.alive():
                    pygame.mixer.init()
                    pygame.mixer.music.load("./musics/winsound.mp3")
                    pygame.mixer.music.play(1)
                    sleep(5)
                    PlaneGame.__game_over() 
            #BOSS在击杀数量达到一定程度时被创建，所以一开始会找不到self.boss
            except AttributeError:
                print("还未出现boss")

    def __event_handler(self):
        for event in pygame.event.get():
            #判断是否退出游戏
            if event.type==pygame.QUIT:
                pygame.quit()
                exit()

            elif event.type==CREATE_ENEMY_EVENT:
                #创建敌机
                enemy=Enemy(self.screen)
                #将敌机添加到敌机组
                self.enemy_group.add(enemy)
            elif event.type==CREATE_SUPERENEMY_EVENT:
                #创建中型敌机
                superenemy=SuperEnemy(self.screen,self.enemy_bullets)
                #纳入中型敌机组
                self.enemy_group.add(superenemy)

            #按空格英雄发射子弹
            elif event.type==pygame.KEYDOWN and event.key==pygame.K_SPACE:
                self.hero.fire()

        #支持按住方向键控制英雄方向
        keys_pressed=pygame.key.get_pressed()
        # 判断元组中对应的按键索引值
        if keys_pressed[pygame.K_RIGHT]:
            self.hero.speed = 2
        elif keys_pressed[pygame.K_LEFT]:
            self.hero.speed = -2
        elif keys_pressed[pygame.K_UP]:
            self.hero.speedh= -2
        elif keys_pressed[pygame.K_DOWN]:
            self.hero.speedh= 2
        else:
            self.hero.speed=0
            self.hero.speedh=0 #不按就没速度
            
    def __check_collide(self):
        #hero bullets and enemies collide then both killed
        pygame.sprite.groupcollide(self.hero.bullets,self.enemy_group,True,True)

        #hero bullets and enemies bullets 不设置both killed

        #hero and enemy collide，后者killed，前者不死
        enemies=pygame.sprite.spritecollide(self.hero, self.enemy_group,True)
        #hero and enemy bullets collide，后者killed，前者不死
        enemies_bullets=pygame.sprite.spritecollide(self.hero, self.enemy_bullets,True)

        #判断列表是否有内容，如果有则把英雄kill
        if len(enemies) or len(enemies_bullets)>0:
            #英雄kill，但不一定死
            self.hero.kill()


    def __check_boss(self):
        ##########全局变量ENEMYCOUNT在plane_sprites模块被定义，在main模块顶部被第一次import############
        ##########由plane_sprites模块下的类方法触发对ENEMYCOUNT数据的+1更新###########################
        ##########过程中在plane_sprites里面打印ENEMYCOUNT可以看到数据+1不断累加#######################
        ##########但是如果在main模块下通过global ENEMYCOUNT访问它，会发现它恒等于初始值0###############
        ##########而如果通过此处import ENEMYCOUNT访问，得到的是正确的累加后的结果#####################
        from plane_sprites import ENEMYCOUNT
        #####因为BOSSCOUNT是在main中被更新，所以不需要重新import##########
        global BOSSCOUNT
        if ENEMYCOUNT>7 and BOSSCOUNT==1:
            BOSSCOUNT +=1
            #消灭达到数量，播放警报音乐，静止2秒
            pygame.mixer.music.load("./musics/alarm.mp3")
            pygame.mixer.music.play(1)
            sleep(2)

            #创建boss，boss加入敌人组
            self.boss=Boss(self.screen,self.enemy_bullets)
            self.enemy_group.add(self.boss)


    def __update_sprites(self):
        self.back_group.update() #背景组中集体update
        self.back_group.draw(self.screen) #把背景组中图像画到surface

        self.enemy_group.update()
        self.enemy_group.draw(self.screen) #敌机组更新和画

        self.hero_group.update()
        self.hero_group.draw(self.screen)  #英雄组

        self.hero.bullets.update()
        self.hero.bullets.draw(self.screen) #英雄子弹组

        self.enemy_bullets.update()
        self.enemy_bullets.draw(self.screen) #敌人子弹组

    #不需要类属性和实例属性的静态方法要通过类名调用哦
    @staticmethod
    def __game_over():   #静态方法不需要self参数
        print("游戏结束")
        pygame.quit()
        exit()




if __name__ == '__main__':
    #创建游戏对象
    game=PlaneGame()

    #启动游戏
    game.start_game()


 


