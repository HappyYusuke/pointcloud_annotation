# pointcloud_annotation

<img width="800" height="1049" alt="image" src="https://github.com/user-attachments/assets/5e5c0eba-5ef9-4d95-8725-cfd36ed86204" />

<br>
<br>

本リポジトリは、[bat-3d](https://github.com/walzimmer/bat-3d.git)のREADMEに情報が足りないため作成しました。
最初に[3d-bat](https://github.com/walzimmer/3d-bat.git)を試しましたが、動作しなかったのでbat-3dの使い方を説明します。
本リポジトリで想定している使用方法は以下の通りですが、本家のREADMEによるとWindowsでも使用できるようです。

内容物
* `base_label_tools.js`, `config.json`, `index.html`
  > bat-3dの設定ファイルたち。
* `input`
  > bat-3dに入れるデータのファイルツリー
* `tools`
  > 点群のファイルの形式を変換するためのツール (READMEあり)

<br>

# Requirements
本リポジトリで想定している環境は以下の通りです。

| 項目 | 要件 |
| --- | --- |
| PC | GPUあり（NVIDIA） |
| OS | Ubuntu22.04 (Windows11でも動作します) |
| Browser | Chrome |
| Data | PointCloud only |

<br>

# Installation
**1. bat-3dと本リポジトリをクローン**
   ```bash
   # bat-3d
   git clone https://github.com/walzimmer/bat-3d.git

   # 本リポジトリ
   git clone https://github.com/HappyYusuke/pointcloud_annotation.git
   ```
   
**2. npmをインストール**
   ```bash
   sudo apt install npm
   ```
   
**3. PHP Stormをダウンロード**</br>
   以下URLからダウンロード（ウィンドウが立ち上がります）</br>
   https://www.jetbrains.com/phpstorm/download/download-thanks.html
   
**4. ファイルを解凍**
   ```bash
   # ダウンロード先に移動
   cd $HOME/Downloads
   
   # 解凍
   tar -zxvf PhpStorm-2025.2.3.tar.gz

   # ホームディレクトリに移動
   mv PhpStorm-252.26830.95 $HOME
   ```
   
**5. 本リポジトリのファイルと置換**
   ```bash
   # ホームディレクトリに移動
   cd $HOME

   # 元のファイルを削除
   rm bat-3d/js/base_label_tool.js bat-3d/config/config.json bat-3d/index.html

   # 本リポジトリのファイルを移動
   mv pointcloud_annotation/base_label_tool.js bat-3d/js
   mv pointcloud_annotation/config.json bat-3d/config
   mv pointcloud_annotation/index.html bat-3d
   ```
   
**6. npmで必要なパッケージをインストール**
   ```bash
   # bat-3dに移動
   cd $HOME/bat-3d

   # パッケージをインストール
   npm install
   ```

<br>

# Usage
## Setup
**1. 独自データを配置** </br>
   本家のREADME通りにファイルツリーを構成し、独自データを格納します。
   <details>
      <summary>ファイルツリーはこちらを参照</summary>
      <pre>
      input
      └── waymo 👉 自分のプロジェクト
          └── 20251015_waymo  👉 シーケンス
              ├── annotations 👉 アノテーション作業の結果格納用
              ├── images      👉 アノテーション作業中に表示される画像格納用（任意）
              ├── pointclouds 👉 点群データを格納（重要）
              │   ├── 000000.pcd
              │   ├── 000001.pcd
              │   ├── 000002.pcd
              │   ├── 000003.pcd
              │   ├── 000004.pcd
              │   ├── 000005.pcd
              │   ├── 000006.pcd
              │   ├── 000007.pcd
              │   ├── 000008.pcd
              │   └── 000009.pcd
              └── pointclouds_without_ground 👉 地面の点を除去したデータ格納用（任意）
      </pre>
   </details>

   ディレクトリを作成
   ```bash
   # 独自データ用のディレクトリをbat-3dに移動
   mv $HOME/pointcloud_annotation/input $HOME/bat-3d

   # bat-3dに移動
   cd $HOME/bat-3d

   # 独自データ用のディレクトリを作成（例：my_data）
   mkdir input/my_data

   # 独自のシーケンス用ディレクトリを作成
   mkdir input/my_data/20251015_my_data

   # 移動
   cd input/my_data/20251015_my_data
   
   # 本家のREADME通りにディレクトリを作成
   mkdir annotations  images  pointclouds  pointclouds_without_ground
   ```

   独自データを格納（⚠️: 点群データは拡張子が`.pcd`です。）
   
   ```bash
   cp /path/to/your/data_directory/*.pcd input/my_data/20251015_my_data/pointclouds
   ```
   
**2. 設定ファイルの編集** </br>
   `bat-3d/config/config.json`の以下の部分を書き換えてください。
   * `name`: ディレクトリ名（例：my_data）
   * `sequences`: シーケンス名（例：20251015_my_data）
   * `classes`: アノテーションするクラス
   * `class_colors`: バウンディングボックスの色
   ```json
   {
      "name": "waymo",
      "sequences": ["20251015_waymo"],
      "classes": ["Car", "Truck", "Motorcycle", "Bicycle", "Pedestrian"],
      "class_colors": ["#51C38C", "#EBCF36", "#B9A454", "#B18CFF", "#E976F9"]
    }
   ```

   `bat-3d/js/base_label_tool.js`の以下の部分を書き換えてください。
   * CUSTOM_DATASET_NAME: ディレクトリ名（例：my_data）
   * CUSTOM_DATASET_NUM_FRAMES: 点群のデータ数
   ```js
   // ==========================================
   // ユーザー用の変数を追加
   // ==========================================
   const CUSTOM_DATASET_NAME = 'waymo';
   const CUSTOM_DATASET_NUM_FRAMES = 5;
   // ==========================================
   ```
   
**3. PHP Storm起動** </br>
   設定ファイルの変更を保存したら、PHP Stormを起動します。
   ```bash
   bash $HOME/PhpStorm-252.26830.95/bin/phpstorm.sh
   ```
   
**4. bat-3d起動** </br>
   * PHP Stormのウィンドウが立ち上がったら、PHP Stormから`bat-3d`のディレクトリを開いてください。
   * ウィンドウ左側のファイルツリーから`index.html`を右クリックしてください。
   * 「開く」 => 「ブラウザ」 => 「Chrome」の順に選択してください。（ブラウザはChrome以外でもOKです）
   * ブラウザでbat-3dが立ち上がります。
   * `Loading (1/hoge) ...` と表示されます。
   * 読み込みが終了したらアノテーションできます。

> [!NOTE]
> ライセンスを求められることがあるが、大学のメールアドレスがあれば[Student Pack](https://www.jetbrains.com/ja-jp/academy/student-pack/?_cl=MTsxOzE7Rmdic3U2Q1RhTThFR2k3eVRrMVRvV3ZnT2xMSGRJRWJMeU5EU0xDSVI5N3RjQ0xxZjJzMERlYmJZbWNDUVM3Rjs=#students)に登録して無料で利用できる。

## How to Annotation
1. `Select View`が`orthographic`の状態でマウスを左クリックしたままスライドする。<br>
すると、バウンディングボックスが表示される。

<img width="400" height="1049" alt="image" src="https://github.com/user-attachments/assets/e368b190-e174-4fde-a900-24c1062322b5" />

</br>
</br>

2. `Cキー`で`Select View`を`perspective`に変更。<br>
マウス操作で視点を変えながらバウンディングボックスの微調整をする。

<img width="400" height="1049" alt="image" src="https://github.com/user-attachments/assets/3a050078-2cb1-4a73-9e1f-854e148115a3" />

</br>
</br>

3. `>`マークをクリックして次のフレームに移動

4. 1.〜3.を繰り返す。

5. `Download Annotations`をクリックする。<br>
ZIPファイルをダウンロードすると、ラベルファイル (JSON) を保存できる。

6. 保存したラベルファイル (JSON) をアノテーションした分だけ`annotation`ディレクトリに移動する。

<br>

# Troubleshooting
## `Loading (1/hoge) ...`で止まる
ここでは、**Chrome**を使用している前提で進めます。

1.  Chromeのアドレスバーに`chrome://settings/system`と入力します。
2.  「**Use hardware acceleration when available** (ハードウェアアクセラレーションが使用可能な場合は使用する)」の設定を探します。
3.  もし設定がONの場合は、一度OFFにしChromeを再起動 => 再度ONにしChromeを再起動。
4.  もし設定がOFFの場合は、ONにし再起動。

> [!NOTE]
> アクセラレーションは`chrome://gpu`で確認できます。<br>
> `WebGL`および`WebGL2`の項目が`Hardware accelerated`と表示されていればGPUが正しく動作しています。

