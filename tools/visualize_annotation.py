import open3d as o3d
import json
import numpy as np
import argparse
import os
import glob

"""
bat-3dでアノテーションした結果を確認するためのプログラム
備考：
bat-3dでのアノテーション結果の確認が信用できないため本プログラムを作成しました
(バウンディングボックスのサイズが違ったり、位置がずれていたりするため)
"""

class AnnotationPlayer:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.pcd_dir = os.path.join(base_dir, "pointclouds")
        self.json_dir = os.path.join(base_dir, "annotations")
        
        # ディレクトリ構造のチェック (bat-3d構成か、フラットか)
        if not os.path.exists(self.pcd_dir):
            print(f"Note: 'pointclouds' folder not found. Assuming flat directory structure.")
            self.pcd_dir = base_dir
            self.json_dir = base_dir

        # PCDファイルリストの取得とソート
        self.pcd_files = sorted(glob.glob(os.path.join(self.pcd_dir, "*.pcd")))
        
        if not self.pcd_files:
            raise FileNotFoundError(f"No .pcd files found in {self.pcd_dir}")
            
        self.num_frames = len(self.pcd_files)
        self.current_idx = 0
        self.geometries = [] # 現在表示中のジオメトリリスト
        
        print(f"Found {self.num_frames} frames.")

    def get_rotation_matrix_z(self, yaw):
        c = np.cos(yaw)
        s = np.sin(yaw)
        return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

    def create_bounding_box(self, label):
        try:
            box3d = label['box3d']
            loc = box3d['location']
            dim = box3d['dimension']
            rot = box3d['orientation']
            
            center = np.array([loc['x'], loc['y'], loc['z']])
            extent = np.array([dim['width'], dim['length'], dim['height']])
            rotation_matrix = self.get_rotation_matrix_z(rot['rotationYaw'])
            
            bbox = o3d.geometry.OrientedBoundingBox(center, rotation_matrix, extent)
            
            # クラスごとの色分け
            category = label.get('category', 'Unknown')
            if category == 'person':
                bbox.color = (1, 0, 1) # マゼンタ
            elif category == 'Car' or category == 'vehicle':
                bbox.color = (0, 1, 0) # 緑
            else:
                bbox.color = (1, 0, 0) # 赤
                
            return bbox
        except Exception as e:
            print(f"Skipping invalid label: {e}")
            return None

    def load_frame(self, idx):
        """指定されたインデックスのジオメトリ（点群＋BBox）をリストで返す"""
        pcd_path = self.pcd_files[idx]
        
        # ファイル名（拡張子なし）を取得してJSONパスを作る
        basename = os.path.splitext(os.path.basename(pcd_path))[0]
        json_path = os.path.join(self.json_dir, basename + ".json")
        
        geoms = []
        
        # 1. 点群の読み込み
        pcd = o3d.io.read_point_cloud(pcd_path)
        if not pcd.has_colors():
            pcd.paint_uniform_color([0.5, 0.5, 0.5])
        geoms.append(pcd)
        
        # 2. JSONの読み込み
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
                labels = data.get('labels', [])
                for label in labels:
                    bbox = self.create_bounding_box(label)
                    if bbox:
                        geoms.append(bbox)
            except Exception as e:
                print(f"Error reading JSON: {e}")
        
        # 3. 座標軸
        axis = o3d.geometry.TriangleMesh.create_coordinate_frame(size=1.0, origin=[0, 0, 0])
        geoms.append(axis)
        
        print(f"Frame [{idx+1}/{self.num_frames}]: {basename}")
        return geoms

    def update_vis(self, vis):
        """Visualizerの内容を更新する"""
        # 古いジオメトリを削除
        for g in self.geometries:
            vis.remove_geometry(g, reset_bounding_box=False)
            
        # 新しいジオメトリを読み込み
        self.geometries = self.load_frame(self.current_idx)
        
        # 新しいジオメトリを追加
        for g in self.geometries:
            vis.add_geometry(g, reset_bounding_box=False)
            
        # 最初のフレームだけ視点をリセット（以降は視点を維持）
        if self.current_idx == 0 and not hasattr(self, 'view_initialized'):
            vis.reset_view_point(True)
            self.view_initialized = True

    def run(self):
        # キーコールバックの定義
        def next_frame(vis):
            if self.current_idx < self.num_frames - 1:
                self.current_idx += 1
                self.update_vis(vis)
            else:
                print("End of sequence.")
            return False

        def prev_frame(vis):
            if self.current_idx > 0:
                self.current_idx -= 1
                self.update_vis(vis)
            else:
                print("Start of sequence.")
            return False

        # キー割り当て
        key_to_callback = {}
        key_to_callback[262] = next_frame # Right Arrow
        key_to_callback[263] = prev_frame # Left Arrow
        # key_to_callback[ord("D")] = next_frame
        # key_to_callback[ord("A")] = prev_frame

        print("Controls:")
        print("  [Right Arrow]: Next Frame")
        print("  [Left Arrow] : Previous Frame")
        print("  [Q]          : Quit")
        
        # 初回読み込み
        self.geometries = self.load_frame(0)

        # 可視化実行
        o3d.visualization.draw_geometries_with_key_callbacks(
            self.geometries,
            key_to_callback,
            window_name="Annotation Player",
            width=1024, height=768
        )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Player for PCD and JSON labels")
    parser.add_argument("dir", help="Path to the sequence directory (containing 'pointclouds' and 'annotations' folders)")
    
    args = parser.parse_args()
    
    try:
        player = AnnotationPlayer(args.dir)
        player.run()
    except Exception as e:
        print(f"Error: {e}")
