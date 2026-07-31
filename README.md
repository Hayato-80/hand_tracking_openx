# hand_tracking_openx

このパッケージは、MediaPipeを用いたハンドトラッキングによってOpenManipulator-Xロボットアームを直感的に操作するためのROS 2パッケージです。

画像ベース・ビジュアルサーボ（IBVS: Image-Based Visual Servoing）のアプローチを採用しており、RealSenseカメラ（またはその他のUSBカメラ）の映像上で、ユーザーの手が常に画面中央にくるようにロボットが滑らかに追従します。

## 主な機能
- **ビジュアルサーボ制御**: 手の位置がカメラフレームの中央にくるように、ロボットアームが自動的にパン（左右）およびピッチ（上下）回転を行い滑らかに追従します。
- **クラッチ（操作の一時停止）機構**: 誤作動を防ぐため、手を「パー（開いた状態）」にしている時のみロボットが追従します。「グー（握った状態）」にすると即座に追従がストップするため、安全に腕の位置を戻すことができます。
- **自動初期位置移動**: 起動時、安全のためロボットは自動的に初期位置（少し上を向いたホームポジション）へ移動してからトラッキングを開始します。

## 動作環境要件
- Ubuntu 24.04 (Noble) 等
- ROS 2 Jazzy
- Python 3.12
- `realsense2_camera` パッケージ
- `open_manipulator` パッケージ一式

### Python 依存パッケージ
Python 3.12ではPEP 668（外部管理環境）が適用されているため、Pythonパッケージは仮想環境（`venv`）内にインストールすることを推奨します。

- `mediapipe` (v0.10.35 または Tasks API 対応バージョン)
- `opencv-python`

## インストール手順

### 1. Python仮想環境（venv）の作成
colconのビルドプロセスと競合しないよう、`ros2_ws`内に`venv`を作成します。

```bash
cd ~/ros2_ws
python3 -m venv --prompt ros2_ws .venv
```

### 2. Python依存関係のインストール
作成した仮想環境を有効化し、MediaPipeとOpenCVをインストールします。

```bash
source ~/ros2_ws/.venv/bin/activate
pip install mediapipe opencv-python
```

### 3. パッケージのビルド
ビルドおよび実行時に仮想環境のパッケージ（site-packages）を参照できるように、`PYTHONPATH` を設定してからビルドを行います。

```bash
cd ~/ros2_ws
export PYTHONPATH=$(python -c 'import site; print(site.getsitepackages()[0])'):$PYTHONPATH
colcon build --packages-select hand_tracking_openx --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
```

*※ この仮想環境を頻繁に利用する場合は、上記の `export PYTHONPATH=...` の行を `~/.bashrc` に追記しておくと便利です。*

## 使い方（起動と操作手順）

### 1. 環境の準備
起動前に、必ずROS 2ワークスペースとPython仮想環境の両方を読み込んでください。

```bash
cd ~/ros2_ws
source install/setup.bash
source .venv/bin/activate
export PYTHONPATH=$(python -c 'import site; print(site.getsitepackages()[0])'):$PYTHONPATH
```

### 2. ノードの起動
以下のLaunchファイルを実行すると、OpenManipulator-Xのコントローラ、RealSenseカメラノード、およびハンドトラッキングノードがすべて自動で立ち上がります。

```bash
ros2 launch hand_tracking_openx hand_tracking_openx.launch.py
```

### 3. 操作方法
1. システムが起動すると、ロボットアームが自動的に初期位置（少し上向き）に移動します。
2. 「Hand Tracking」というウィンドウが開き、カメラの映像と中央に赤い十字マーク（ターゲット）が表示されます。
3. カメラに手をかざします。
4. **【追従開始】**: 手を「パー（開く）」にしてください。ロボットが赤い十字マークを手首の位置に合わせるように滑らかに動き出します。
5. **【追従停止】**: 手を「グー（握る）」にしてください。ロボットの追従がその場でピタッと停止します。
6. **【終了方法】**: ターミナル上で `Ctrl+C` を **1回だけ** 押し、数秒間お待ちください。すべてのノードが安全かつクリーンに終了します。（連打するとゾンビプロセスが残る原因になるためご注意ください）
