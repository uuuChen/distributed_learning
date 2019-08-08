﻿# distributed_learning
--------------------------------------------
--------------------------------------------
## 初始 origin 參數 (只需執行一次）
1. git remote add origin https://github.com/uuuChen/distributed_learning  
--------------------------------------------
## 上傳
1. git add . <br>
2. git commit -m "commit message" <br>
3. git push <br>

--------------------------------------------
## 更新
1. git pull <br>

## 強制更新
1. git reset --hard <br>
2. git pull <br>

--------------------------------------------
## 目前進度

####  "vim MNIST_dataSet.py" | Edward1997 | 08/08
1. 改為從 torchvision 下載本地端資料
2. 從資料庫讀資料改為一次全部讀取
3. 增加資料前處理(mongodb --> model 之間時處理) 

####  "add LeNet.py" | Edward1997 | 08/08

####  "vim MNIST_train.py" | Edward1997 | 08/08
1. 參數調整: lr = 0.01 , batch_size = 128 , momentum = 0.9
2. 改用 LeNet模型
3. loss function 改用 cross_entropy()
4. 增加繪圖程式碼，但目前為註解狀態未啟用

####  "delet MNIST_data directory" , "add MNIST directory" | Edward1997 | 08/08
1.更動本地存放之資料路徑與內容

####  "add readme.md" | uuuChen | 08/06
1. 增加 readme.md 
2. 更動 "train.py" argparse 初始方式 

####  "add train directory" | uuuChen | 08/06
1. 在 “train/” 創建對應 MNIST、DRD、ECG 的 python 檔，方便參數管理<br>

#### "ECG train successfully" | uuuChen | 08/06
1. ECG 以 MLP train 成功，test dataSet 在第三個 epoch 的正確率大概 93%<br>
2. 將 MNIST_train.py、DRD_train.py 的 model 放到 global，讓 train 跟
 test 時都使用同樣的 model。原先的做法在 test 時無法使用已被 train 更新的 model<br>
3. MNIST 以 MLP 訓練，在 test 時的正確率也可到達 90% ，可嘗試將 model 以 Lenet 替換
--------------------------------------------
