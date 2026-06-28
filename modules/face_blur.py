"""顔検出＋ぼかし処理モジュール（MediaPipe + OpenCV）"""
import cv2
import mediapipe as mp
from pathlib import Path

mp_face = mp.solutions.face_detection


def blur_faces(image_path: str, output_path: str | None = None, blur_strength: int = 51) -> str:
    """
    画像内の顔を検出してぼかし処理する。
    output_path が None の場合、元ファイル名に _blurred を付けて同じフォルダに保存。
    処理後のファイルパスを返す。
    """
    src = Path(image_path)
    if not src.exists():
        raise FileNotFoundError(f"画像が見つかりません: {image_path}")

    img = cv2.imread(str(src))
    if img is None:
        raise ValueError(f"画像を読み込めませんでした: {image_path}")

    h, w = img.shape[:2]
    face_count = 0

    with mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.5) as detector:
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = detector.process(rgb)

        if results.detections:
            for detection in results.detections:
                box = detection.location_data.relative_bounding_box
                x = max(0, int(box.xmin * w))
                y = max(0, int(box.ymin * h))
                bw = min(int(box.width * w), w - x)
                bh = min(int(box.height * h), h - y)

                # 余白を少し広げて顔全体をカバー
                padding_x = int(bw * 0.15)
                padding_y = int(bh * 0.2)
                x1 = max(0, x - padding_x)
                y1 = max(0, y - padding_y)
                x2 = min(w, x + bw + padding_x)
                y2 = min(h, y + bh + padding_y)

                face_roi = img[y1:y2, x1:x2]
                k = blur_strength if blur_strength % 2 == 1 else blur_strength + 1
                blurred = cv2.GaussianBlur(face_roi, (k, k), 0)
                img[y1:y2, x1:x2] = blurred
                face_count += 1

    if output_path is None:
        dest = src.parent / f"{src.stem}_blurred{src.suffix}"
    else:
        dest = Path(output_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

    cv2.imwrite(str(dest), img)
    return str(dest), face_count


def blur_folder(folder_path: str, output_folder: str | None = None, blur_strength: int = 51) -> list[dict]:
    """
    フォルダ内の全画像をぼかし処理する。
    結果のリスト（ファイルパス・検出顔数）を返す。
    """
    src_dir = Path(folder_path)
    extensions = {".jpg", ".jpeg", ".png", ".gif"}
    images = [f for f in src_dir.iterdir() if f.suffix.lower() in extensions]

    if not images:
        raise ValueError(f"画像ファイルが見つかりません: {folder_path}")

    if output_folder:
        out_dir = Path(output_folder)
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = src_dir / "blurred"
        out_dir.mkdir(exist_ok=True)

    results = []
    for img_path in images:
        out_path = out_dir / img_path.name
        dest, count = blur_faces(str(img_path), str(out_path), blur_strength)
        results.append({"input": str(img_path), "output": dest, "faces": count})

    return results
