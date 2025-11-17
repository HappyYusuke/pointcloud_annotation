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
        
        if not os.path.exists(self.pcd_dir):
            print(f"Note: 'pointclouds' folder not found. Assuming flat directory structure.")
            self.pcd_dir = base_dir
            self.json_dir = base_dir

        self.pcd_files = sorted(glob.glob(os.path.join(self.pcd_dir, "*.pcd")))
        
        if not self.pcd_files:
            raise FileNotFoundError(f"No .pcd files found in {self.pcd_dir}")
            
        self.num_frames = len(self.pcd_files)
        self.current_idx = 0
        
        # 描画管理用
        self.geometries = []       # 現在Visualizerに登録されているジオメトリ
        self.current_pcd = None    # 現在の生の点群データ
        self.current_bboxes = []   # 現在のバウンディングボックスリスト
        self.axis = o3d.geometry.TriangleMesh.create_coordinate_frame(size=1.0, origin=[0, 0, 0])
        
        # 表示モードフラグ (TrueならBBox内のみ表示)
        self.is_cropped_view = False

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
            
            category = label.get('category', 'Unknown')
            if category == 'person':
                bbox.color = (1, 0, 1) 
            elif category == 'Car' or category == 'vehicle':
                bbox.color = (0, 1, 0) 
            else:
                bbox.color = (1, 0, 0) 
                
            return bbox
        except Exception as e:
            return None

    def load_data(self, idx):
        """指定インデックスのデータを読み込んでメンバ変数を更新する"""
        pcd_path = self.pcd_files[idx]
        basename = os.path.splitext(os.path.basename(pcd_path))[0]
        json_path = os.path.join(self.json_dir, basename + ".json")
        
        # 1. 点群読み込み
        self.current_pcd = o3d.io.read_point_cloud(pcd_path)
        if not self.current_pcd.has_colors():
            self.current_pcd.paint_uniform_color([0.5, 0.5, 0.5])
        
        # 2. BBox読み込み
        self.current_bboxes = []
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
                labels = data.get('labels', [])
                for label in labels:
                    bbox = self.create_bounding_box(label)
                    if bbox:
                        self.current_bboxes.append(bbox)
            except Exception:
                pass
        
        print(f"Frame [{idx+1}/{self.num_frames}]: {basename} (BBoxes: {len(self.current_bboxes)})")

    def get_render_geometries(self):
        """現在のモードに合わせて表示すべきジオメトリのリストを返す"""
        geoms = [self.axis]
        geoms.extend(self.current_bboxes)

        if self.is_cropped_view and self.current_bboxes:
            # クロップモード: 各BBoxの中身を切り出して結合
            cropped_pcd_combined = o3d.geometry.PointCloud()
            for bbox in self.current_bboxes:
                # 点群をBBoxで切り抜く
                cropped_part = self.current_pcd.crop(bbox)
                cropped_pcd_combined += cropped_part
            
            geoms.append(cropped_pcd_combined)
        else:
            # 通常モード: 全点群を表示
            geoms.append(self.current_pcd)
            
        return geoms

    def update_vis(self, vis):
        """Visualizerの更新処理"""
        # 1. 現在登録されているジオメトリを削除
        for g in self.geometries:
            vis.remove_geometry(g, reset_bounding_box=False)
        
        # 2. 表示すべきジオメトリを取得
        self.geometries = self.get_render_geometries()
        
        # 3. 新しいジオメトリを追加
        for g in self.geometries:
            vis.add_geometry(g, reset_bounding_box=False)
            
        # 初回のみ視点リセット
        if self.current_idx == 0 and not hasattr(self, 'view_initialized'):
            vis.reset_view_point(True)
            self.view_initialized = True

    def run(self):
        def next_frame(vis):
            if self.current_idx < self.num_frames - 1:
                self.current_idx += 1
                self.load_data(self.current_idx)
                self.update_vis(vis)
            return False

        def prev_frame(vis):
            if self.current_idx > 0:
                self.current_idx -= 1
                self.load_data(self.current_idx)
                self.update_vis(vis)
            return False

        def toggle_crop(vis):
            self.is_cropped_view = not self.is_cropped_view
            mode_str = "Cropped View" if self.is_cropped_view else "Full View"
            print(f"Switched to: {mode_str}")
            self.update_vis(vis)
            return False

        key_to_callback = {}
        key_to_callback[262] = next_frame # Right Arrow
        key_to_callback[263] = prev_frame # Left Arrow
        key_to_callback[ord("D")] = toggle_crop # D key

        print("Controls:")
        print("  [Right Arrow]: Next Frame")
        print("  [Left Arrow] : Previous Frame")
        print("  [D]          : Toggle Cropped View (BBox points only)")
        print("  [Q]          : Quit")
        
        # 初回データロード
        self.load_data(0)
        
        # 初回表示用のジオメトリリストをここで作成
        self.geometries = self.get_render_geometries()

        o3d.visualization.draw_geometries_with_key_callbacks(
            self.geometries,
            key_to_callback,
            window_name="Annotation Player",
            width=1024, height=768
        )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Player for PCD and JSON labels")
    parser.add_argument("dir", help="Path to the sequence directory")
    args = parser.parse_args()
    
    try:
        player = AnnotationPlayer(args.dir)
        player.run()
    except Exception as e:
        print(f"Error: {e}")
