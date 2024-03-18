from game.logic.base import BaseLogic
from game.models import Board, GameObject
import math

# Kalo kepanjangan namanya bisa disingkat FTKFTE
class FirstToTheKeyFirstToTheEggBot(BaseLogic):
    
    targetX = 99
    targetY = 99
    tele1_step = 99
    tele1_X = 99
    tele1_Y = 99
    tele2_step = 99
    tele2_X = 99
    tele2_Y = 99
    
    def __init__(self):
        self.targetX = 99
        self.targetY = 99
        self.tele1_step = 99
        self.tele1_X = 99
        self.tele1_Y = 99
        self.tele2_step = 99
        self.tele2_X = 99
        self.tele2_Y = 99
    
    # Mengiterasi objek untuk mencari objek bertipe diamond, teleporter, dan button
    def getObjectsPosition(self,board_bot:GameObject,board:Board):
        target_X = 99
        target_Y = 99
        
        currX = board_bot.position.x
        currY = board_bot.position.y
        
        diamond_min_step = 99
        shortest_diamond_X = 99
        shortest_diamond_Y = 99
        n_diamond = 0
        
        button_step = 99
        button_X = 99
        button_Y = 99
        button_radar = 3
        diamond_in_button_radar = 0
        
        isTele1 = True

        # Iterasi objek
        for object in board.game_objects:
            # Dapatkan info diamond terdekat
            if object.type == "DiamondGameObject":
                n_diamond+=1
                if abs(object.position.x-button_X)+abs(object.position.y-button_Y) <= button_radar:
                    diamond_in_button_radar+=1
                # Teleporter (objek bertipe teleporter selalu berada di awal sehingga data teleporter sudah didapatkan terlebih dahulu)
                step_in_tele1 = (abs(currX-self.tele1_X)+abs(currY-self.tele1_Y))+(abs(self.tele2_X-object.position.x)+abs(self.tele2_Y-object.position.y))
                step_in_tele2 = (abs(currX-self.tele2_X)+abs(currY-self.tele2_Y))+(abs(self.tele1_X-object.position.x)+abs(self.tele1_Y-object.position.y))
                # Original
                temp_step = abs(object.position.y-board_bot.position.y) + abs(object.position.x-board_bot.position.x)
                # Menentukan step terpendek
                diamond_min_step_temp = min(temp_step,step_in_tele1,step_in_tele2)
                if diamond_min_step_temp < diamond_min_step:
                    diamond_min_step = diamond_min_step_temp
                    # Penentuan posisi koordinat target
                    if diamond_min_step == step_in_tele1:
                        shortest_diamond_X = self.tele1_X
                        shortest_diamond_Y = self.tele1_Y
                    elif diamond_min_step == step_in_tele2:
                        shortest_diamond_X = self.tele2_X
                        shortest_diamond_Y = self.tele2_Y
                    else:
                        shortest_diamond_X = object.position.x
                        shortest_diamond_Y = object.position.y
            # Dapatkan info teleporter
            elif object.type == "TeleportGameObject":
                # objek bertipe teleporter yang pertama ditemukan saat loop dianggap sebagai Tele1
                if isTele1:
                    self.tele1_X = object.position.x
                    self.tele1_Y = object.position.y
                    self.tele1_step = abs(object.position.x-currX)+abs(object.position.y-currY)
                    isTele1 = False
                else:
                    self.tele2_X = object.position.x
                    self.tele2_Y = object.position.y
                    self.tele2_step = abs(object.position.x-currX)+abs(object.position.y-currY)
            # Dapatkan info button        
            elif object.type == "DiamondButtonGameObject":
                button_X = object.position.x
                button_Y = object.position.y
                button_step_temp = abs(currX-button_X)+abs(currY-button_Y)
                button_step_tele1 = (abs(currX-self.tele1_X)+abs(currY-self.tele1_Y))+(abs(self.tele2_X-object.position.x)+abs(self.tele2_Y-object.position.y))
                button_step_tele2 = (abs(currX-self.tele2_X)+abs(currY-self.tele2_Y))+(abs(self.tele1_X-object.position.x)+abs(self.tele1_Y-object.position.y))
                button_step = min(button_step_temp,button_step_tele2,button_step_tele1)
                if button_step == button_step_tele1:
                    button_X = self.tele1_X
                    button_Y = self.tele1_Y
                elif button_step == button_step_tele2:
                    button_X = self.tele2_X
                    button_Y = self.tele2_Y
                else:
                    button_X = object.position.x
                    button_Y = object.position.y
    
        if n_diamond == 1:
            # Jika sisa diamond pada board adalah 1 dan jumlah diamond saat ini adalah 0
            # Maka targetnya adalah pergi ke tengah dan bersiap untuk reset diamond
            # setelah diamond terakhir diambil orang lain
            # atau pergi ke button jika button lebih dekat dengan kita
            if board_bot.properties.diamonds == 0:
                step_to_center = abs(7-currX)+abs(7-currY)
                if step_to_center < button_step:
                    target_X = 7
                    target_Y = 7
                else:
                    target_X = button_X
                    target_Y = button_Y      
            # Jika sisa diamond pada board adalah 1 dan jumlah diamond saat ini > 0
            # Maka lebih baik mengamankan terlebih dahulu ke base
            else:
                target_X = board_bot.properties.base.x
                target_Y = board_bot.properties.base.y
        else:
            min_step = min(diamond_min_step,button_step)
            # Pergi ke button jika dan hanya jika:
            # 1. Button adalah yang terdekat dan
            # 2. Tidak ada diamond sama sekali di sekitar button dengan jarak 3 langkah dari button dan
            # 3. Diamond saat ini < 4
            if min_step == button_step and diamond_in_button_radar == 0 and board_bot.properties.diamonds < 4 :
                target_X = button_X
                target_Y = button_Y
            else:
                target_X = shortest_diamond_X
                target_Y = shortest_diamond_Y
        return (target_X, target_Y)
        
    # Fungsi untuk mengiterasi objek bot lain dan menentukan apakah akan mencoba
    # melakukan tackle atau tidak
    def tackle(self,board_bot:GameObject,board:Board):
        currX = board_bot.position.x
        currY = board_bot.position.y
        
        isTackle = False
        dx = 0
        dy = 0
        
        # Iterasi bot
        for bot in board.bots:
            # Hanya bot dengan diamond > 2 yang diperhitungkan
            if bot.properties.diamonds > 2:
                tackleX = bot.position.x-currX
                tackleY = bot.position.y-currY
                if (tackleX == 1 or tackleX == -1) and tackleY==0:
                    dx = tackleX
                    isTackle = True
                    break
                if (tackleY == 1 or tackleY == -1) and tackleX==0:
                    dy = tackleY
                    isTackle = True
                    break
        return (dx,dy,isTackle)
            
    def next_move(self, board_bot: GameObject, board: Board):
        # Mencoba tackle hanya jika diamond saat ini < 2
        if board_bot.properties.diamonds < 2:
            tackle = self.tackle(board_bot,board)
            if tackle[2]:
                return tackle[0], tackle[1]
        # Iterate objects
        tempXY = self.getObjectsPosition(board_bot,board)
        delta_x = 0
        delta_y = 0
        threshold = 4 # Maximum iteration to decide delta_x and delta_y
        count = 0
        self.targetX = tempXY[0]
        self.targetY = tempXY[1]
        # Iterate
        # Iteration might be done if the bot arrived at target position
        while(delta_x == 0 and delta_y == 0 and count < threshold):         
            currX = board_bot.position.x
            currY = board_bot.position.y
            # Hitung langkah kembali ke base dengan cara biasa dan dengan teleporter
            original_step = abs(board_bot.position.x-board_bot.properties.base.x)+abs(board_bot.position.y-board_bot.properties.base.y)
            tele1_step = (abs(currX-self.tele1_X)+abs(currY-self.tele1_Y))+(abs(board_bot.properties.base.x-self.tele2_X)+abs(board_bot.properties.base.y-self.tele2_Y))
            tele2_step = (abs(currX-self.tele2_X)+abs(currY-self.tele2_Y))+(abs(board_bot.properties.base.x-self.tele1_X)+abs(board_bot.properties.base.y-self.tele1_Y))
            min_target_step = min(original_step,tele1_step,tele2_step)
            
            # Endgame : Jika selisih antara sisa waktu permainan 
            # dan langkah untuk kembali ke base = 2, maka kembali ke base
            if ((((board_bot.properties.milliseconds_left//1000))-min_target_step) <= 2):
                if min_target_step == tele1_step:
                    self.targetX = self.tele1_X
                    self.targetY = self.tele1_Y
                elif min_target_step == tele2_step:
                    self.targetX = self.tele2_X
                    self.targetY = self.tele2_Y
                else:
                    self.targetX = board_bot.properties.base.x
                    self.targetY = board_bot.properties.base.y

                if(self.targetX!=99):
                    if self.targetX < currX:
                        delta_x = -1
                        break
                    elif self.targetX > currX:
                        delta_x = 1
                        break
                    else:
                        self.targetX = 99
                                    
                if(self.targetY!=99):
                    if self.targetY < currY:
                        delta_y = -1
                        break
                    elif self.targetY > currY:
                        delta_y = 1
                        break
                    else:
                        self.targetY = 99
            # Jika diamond di inventory sudah ada 4 atau 5 maka kembali ke base
            elif (board_bot.properties.diamonds > 3):
                # Hitung langkah kembali ke base dengan cara biasa dan dengan teleporter
                original_step = abs(currX-board_bot.properties.base.x)+abs(currY-board_bot.properties.base.y)
                tele1_step = (abs(currX-self.tele1_X)+abs(currY-self.tele1_Y))+(abs(board_bot.properties.base.x-self.tele2_X)+abs(board_bot.properties.base.y-self.tele2_Y))
                tele2_step = (abs(currX-self.tele2_X)+abs(currY-self.tele2_Y))+(abs(board_bot.properties.base.x-self.tele1_X)+abs(board_bot.properties.base.y-self.tele1_Y))
                min_target_step = min(original_step,tele1_step,tele2_step)
                if min_target_step == tele1_step:
                    self.targetX = self.tele1_X
                    self.targetY = self.tele1_Y
                elif min_target_step == tele2_step:
                    self.targetX = self.tele2_X
                    self.targetY = self.tele2_Y
                else:  
                    self.targetX = board_bot.properties.base.x
                    self.targetY = board_bot.properties.base.y
                
                if(self.targetX!=99):
                    if self.targetX < currX:
                        delta_x = -1
                        break
                    elif self.targetX > currX:
                        delta_x = 1
                        break
                    else:
                        self.targetX = 99
                                    
                if(self.targetY!=99):
                    if self.targetY < currY:
                        delta_y = -1
                        break
                    elif self.targetY > currY:
                        delta_y = 1
                        break
                    else:
                        self.targetY = 99
            else:
                if(self.targetX!=99):
                    if self.targetX < currX:
                        delta_x = -1
                        break
                    elif self.targetX > currX:
                        delta_x = 1
                        break
                    else:
                        self.targetX = 99
                                    
                if(self.targetY!=99):
                    if self.targetY < currY:
                        delta_y = -1
                        break
                    elif self.targetY > currY:
                        delta_y = 1
                        break
                    else:
                        self.targetY = 99
                
            if(self.targetX!=99):
                if self.targetX < currX:
                    delta_x = -1
                    break
                elif self.targetX > currX:
                    delta_x = 1
                    break
                else:
                    self.targetX = 99
                                
            if(self.targetY!=99):
                if self.targetY < currY:
                    delta_y = -1
                    break
                elif self.targetY > currY:
                    delta_y = 1
                    break
                else:
                    self.targetY = 99        
            count+=1    

        # Handling jika ternyata setelah hasil iterasi delta_x = delta_y
        if (delta_x == delta_y):
            if currX == 0:
                delta_x = 1
                delta_y = 0
            elif currX == 14:
                delta_x = -1
                delta_y = 0
            elif currY == 0:
                delta_x = 0
                delta_y = 1
            elif currY == 14:
                delta_x = 0
                delta_y = -1
            else:
                delta_x = 1
                delta_y = 0
                
        return delta_x, delta_y
    