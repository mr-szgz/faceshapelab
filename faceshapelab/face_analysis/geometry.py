# Adapted from VisoMaster-Fusion, commit 6563cd21322cf413d0b391aa552f383339636595.
# SPDX-License-Identifier: GPL-3.0-only
import cv2
import kornia.geometry.transform as kgm
import numpy as np
import torch
from skimage import transform as trans
from torchvision.transforms import v2

LANDMARK_314_EYE_LEFT = 312
LANDMARK_314_EYE_RIGHT = 313
LANDMARK_314_NOSE_TIP = 154
LANDMARK_314_LIP_LEFT = 51
LANDMARK_314_LIP_RIGHT = 258
LANDMARK_314_EYE_LEFT_CORNERS = [28, 126]
LANDMARK_314_EYE_RIGHT_CORNERS = [186, 283]


src1 = np.array(
    [
        [51.642, 50.115],
        [57.617, 49.99],
        [35.74, 69.007],
        [51.157, 89.05],
        [57.025, 89.702],
    ],
    dtype=np.float32,
)

src2 = np.array(
    [
        [45.031, 50.118],
        [65.568, 50.872],
        [39.677, 68.111],
        [45.177, 86.19],
        [64.246, 86.758],
    ],
    dtype=np.float32,
)

src3 = np.array(
    [
        [39.73, 51.138],
        [72.27, 51.138],
        [56.0, 68.493],
        [42.463, 87.01],
        [69.537, 87.01],
    ],
    dtype=np.float32,
)

src4 = np.array(
    [
        [46.845, 50.872],
        [67.382, 50.118],
        [72.737, 68.111],
        [48.167, 86.758],
        [67.236, 86.19],
    ],
    dtype=np.float32,
)

src5 = np.array(
    [
        [54.796, 49.99],
        [60.771, 50.115],
        [76.673, 69.007],
        [55.388, 89.702],
        [61.257, 89.05],
    ],
    dtype=np.float32,
)

src6 = np.array(
    [[39.73, 55.0], [72.27, 55.0], [56.0, 64.0], [42.463, 78.0], [69.537, 78.0]],
    dtype=np.float32,
)

src7 = np.array(
    [[39.73, 45.0], [72.27, 45.0], [56.0, 75.0], [42.463, 95.0], [69.537, 95.0]],
    dtype=np.float32,
)

src = np.array([src1, src2, src3, src4, src5, src6, src7])

src_map = {112: src, 224: src * 2}

arcface_src = np.array(
    [
        [38.2946, 51.6963],
        [73.5318, 51.5014],
        [56.0252, 71.7366],
        [41.5493, 92.3655],
        [70.7299, 92.2041],
    ],
    dtype=np.float32,
)

arcface_src = np.expand_dims(arcface_src, axis=0)


def pad_image_by_size(img, image_size):
    if not isinstance(image_size, tuple):
        image_size = (image_size, image_size)
    w, h = (img.size(dim=2), img.size(dim=1))
    target_h, target_w = image_size
    if w < target_w or h < target_h:
        pad_right = max(target_w - w, 0)
        pad_bottom = max(target_h - h, 0)
        img = torch.nn.functional.pad(
            img, (0, pad_right, 0, pad_bottom), mode="constant", value=0
        )
    return img


def transform(img, center, output_size, scale, rotation):
    img = pad_image_by_size(img, output_size)
    scale_ratio = scale
    rot = float(rotation) * np.pi / 180.0
    t1 = trans.SimilarityTransform(scale=scale_ratio)
    cx = center[0] * scale_ratio
    cy = center[1] * scale_ratio
    t2 = trans.SimilarityTransform(translation=(-1 * cx, -1 * cy))
    t3 = trans.SimilarityTransform(rotation=rot)
    t4 = trans.SimilarityTransform(translation=(output_size / 2, output_size / 2))
    t = t1 + t2 + t3 + t4
    M = t.params[0:2]
    M_tensor = torch.from_numpy(M).float().unsqueeze(0).to(img.device)
    img_b = img.unsqueeze(0) if img.dim() == 3 else img
    cropped = kgm.warp_affine(
        img_b.float(),
        M_tensor,
        dsize=(output_size, output_size),
        mode="bilinear",
        align_corners=True,
    ).squeeze(0)
    return (cropped.to(img.dtype), M)


def trans_points2d(pts, M):
    ones_column = np.ones((pts.shape[0], 1), dtype=np.float32)
    homogeneous_pts = np.hstack([pts, ones_column])
    transformed_pts = np.dot(homogeneous_pts, M.T)
    return transformed_pts[:, :2]


def trans_points3d(pts, M):
    scale = np.sqrt(M[0, 0] ** 2 + M[0, 1] ** 2)
    ones_column = np.ones((pts.shape[0], 1), dtype=np.float32)
    homogeneous_pts = np.hstack([pts[:, :2], ones_column])
    transformed_2d = np.dot(homogeneous_pts, M.T)
    scaled_z = pts[:, 2] * scale
    transformed_pts = np.hstack([transformed_2d[:, :2], scaled_z.reshape(-1, 1)])
    return transformed_pts


def trans_points(pts, M):
    if pts.shape[1] == 2:
        return trans_points2d(pts, M)
    else:
        return trans_points3d(pts, M)


def estimate_norm(lmk, image_size=112, mode="arcface112"):
    lmk_tran = np.insert(lmk, 2, values=np.ones(5), axis=1)
    min_M = []
    min_index = []
    min_error = float("inf")
    if mode != "arcfacemap":
        if mode == "arcface112":
            src = float(image_size) / 112.0 * arcface_src
        else:
            factor = float(image_size) / 128.0
            src = arcface_src.copy() * factor
            src[:, :, 0] += factor * 8.0
    else:
        src = float(image_size) / 112.0 * src_map[112]
    for i in np.arange(src.shape[0]):
        tform = trans.SimilarityTransform.from_estimate(lmk, src[i])
        M = tform.params[0:2, :]
        results = np.dot(M, lmk_tran.T)
        results = results.T
        error = np.sum(np.sqrt(np.sum((results - src[i]) ** 2, axis=1)))
        if error < min_error:
            min_error = error
            min_M = M
            min_index = i
    return (min_M, min_index)


def warp_face_by_face_landmark_5(
    img,
    kpss,
    image_size=112,
    mode="arcface112",
    interpolation=v2.InterpolationMode.NEAREST,
):
    img = pad_image_by_size(img, image_size)
    M, _ = estimate_norm(kpss, image_size, mode=mode)
    M_tensor = torch.from_numpy(M).float().unsqueeze(0).to(img.device)
    img_b = img.unsqueeze(0) if img.dim() == 3 else img
    mode_kgm = (
        "nearest" if interpolation == v2.InterpolationMode.NEAREST else "bilinear"
    )
    img_warped = kgm.warp_affine(
        img_b.float(),
        M_tensor,
        dsize=(image_size, image_size),
        mode=mode_kgm,
        align_corners=True,
    ).squeeze(0)
    return (img_warped.to(img.dtype), M)


def invertAffineTransform(M):
    M_H = np.vstack([M, np.array([0, 0, 1])])
    IM = np.linalg.inv(M_H)
    return IM[0:2, :]


def warp_face_by_bounding_box_for_landmark_68(img, bbox, input_size):
    img = pad_image_by_size(img, input_size[0])
    scale = 195 / np.subtract(bbox[2:], bbox[:2]).max()
    translation = (256 - np.add(bbox[2:], bbox[:2]) * scale) * 0.5
    affine_matrix = np.array([[scale, 0, translation[0]], [0, scale, translation[1]]])
    M_tensor = torch.from_numpy(affine_matrix).float().unsqueeze(0).to(img.device)
    img_b = img.unsqueeze(0) if img.dim() == 3 else img
    crop_image = (
        kgm.warp_affine(
            img_b.float(),
            M_tensor,
            dsize=(input_size[1], input_size[0]),
            mode="bilinear",
            align_corners=True,
        )
        .squeeze(0)
        .to(img.dtype)
    )
    if torch.mean(crop_image.to(dtype=torch.float32)[0, :, :]) < 30:
        lab = cv2.cvtColor(
            crop_image.permute(1, 2, 0).to("cpu").numpy(), cv2.COLOR_RGB2Lab
        )
        clahe = cv2.createCLAHE(clipLimit=2)
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        crop_image = (
            torch.from_numpy(cv2.cvtColor(lab, cv2.COLOR_Lab2RGB))
            .to(img.device)
            .permute(2, 0, 1)
        )
    return (crop_image, affine_matrix)


def warp_face_by_bounding_box_for_landmark_98(img, bbox_org, input_size):
    img = pad_image_by_size(img, input_size[0])
    bbox = bbox_org.copy()
    min_face = 20
    base_extend_range = [0.2, 0.3]
    bbox_width = bbox[2] - bbox[0]
    bbox_height = bbox[3] - bbox[1]
    if bbox_width <= min_face or bbox_height <= min_face:
        return (None, None)
    add = int(max(bbox_width, bbox_height))
    bimg = torch.nn.functional.pad(img, (add, add, add, add), "constant", 0)
    bbox += add
    face_width = (1 + 2 * base_extend_range[0]) * bbox_width
    center = [(bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2]
    bbox[0] = center[0] - face_width // 2
    bbox[1] = center[1] - face_width // 2
    bbox[2] = center[0] + face_width // 2
    bbox[3] = center[1] + face_width // 2
    bbox = bbox.astype(np.int32)
    crop_image = bimg[:, bbox[1] : bbox[3], bbox[0] : bbox[2]]
    h, w = (crop_image.size(dim=1), crop_image.size(dim=2))
    t_resize = v2.Resize((input_size[1], input_size[0]), antialias=False)
    crop_image = t_resize(crop_image)
    return (crop_image, [h, w, bbox[1], bbox[0], add])


def convert_face_landmark_68_to_5(face_landmark_68, face_landmark_68_score):
    lm_idx = np.array([31, 37, 40, 43, 46, 49, 55], dtype=np.int32) - 1
    face_landmark_5 = np.stack(
        [
            np.mean(face_landmark_68[lm_idx[[1, 2]], :], 0),
            np.mean(face_landmark_68[lm_idx[[3, 4]], :], 0),
            face_landmark_68[lm_idx[0], :],
            face_landmark_68[lm_idx[5], :],
            face_landmark_68[lm_idx[6], :],
        ],
        axis=0,
    )
    if np.any(face_landmark_68_score):
        face_landmark_5_score = np.stack(
            [
                np.mean(face_landmark_68_score[lm_idx[[1, 2]], :], 0),
                np.mean(face_landmark_68_score[lm_idx[[3, 4]], :], 0),
                face_landmark_68_score[lm_idx[0], :],
                face_landmark_68_score[lm_idx[5], :],
                face_landmark_68_score[lm_idx[6], :],
            ],
            axis=0,
        )
    else:
        face_landmark_5_score = np.array([])
    return (face_landmark_5, face_landmark_5_score)


def convert_face_landmark_98_to_5(face_landmark_98, face_landmark_98_score):
    face_landmark_5 = np.array(
        [
            face_landmark_98[96],
            face_landmark_98[97],
            face_landmark_98[54],
            face_landmark_98[76],
            face_landmark_98[82],
        ]
    )
    face_landmark_5_score = np.array(
        [
            face_landmark_98_score[96],
            face_landmark_98_score[97],
            face_landmark_98_score[54],
            face_landmark_98_score[76],
            face_landmark_98_score[82],
        ]
    )
    return (face_landmark_5, face_landmark_5_score)


def convert_face_landmark_314_to_5(
    face_landmark_314: np.ndarray,
    face_landmark_314_score: np.ndarray,
    use_mean_eyes: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    if use_mean_eyes:
        eye_left = np.mean(face_landmark_314[LANDMARK_314_EYE_LEFT_CORNERS], axis=0)
        eye_right = np.mean(face_landmark_314[LANDMARK_314_EYE_RIGHT_CORNERS], axis=0)
        eye_left_score = (
            np.mean(face_landmark_314_score[LANDMARK_314_EYE_LEFT_CORNERS])
            if len(face_landmark_314_score) > 0
            else 0.0
        )
        eye_right_score = (
            np.mean(face_landmark_314_score[LANDMARK_314_EYE_RIGHT_CORNERS])
            if len(face_landmark_314_score) > 0
            else 0.0
        )
    else:
        eye_left = face_landmark_314[LANDMARK_314_EYE_LEFT]
        eye_right = face_landmark_314[LANDMARK_314_EYE_RIGHT]
        eye_left_score = (
            face_landmark_314_score[LANDMARK_314_EYE_LEFT]
            if len(face_landmark_314_score) > 0
            else 0.0
        )
        eye_right_score = (
            face_landmark_314_score[LANDMARK_314_EYE_RIGHT]
            if len(face_landmark_314_score) > 0
            else 0.0
        )
    nose = face_landmark_314[LANDMARK_314_NOSE_TIP]
    lip_left = face_landmark_314[LANDMARK_314_LIP_LEFT]
    lip_right = face_landmark_314[LANDMARK_314_LIP_RIGHT]
    face_landmark_5 = np.array([eye_left, eye_right, nose, lip_left, lip_right])
    if len(face_landmark_314_score) > 0:
        face_landmark_5_score = np.array(
            [
                eye_left_score,
                eye_right_score,
                face_landmark_314_score[LANDMARK_314_NOSE_TIP],
                face_landmark_314_score[LANDMARK_314_LIP_LEFT],
                face_landmark_314_score[LANDMARK_314_LIP_RIGHT],
            ]
        )
    else:
        face_landmark_5_score = np.array([])
    return (face_landmark_5, face_landmark_5_score)


def convert_face_landmark_106_to_5(face_landmark_106):
    face_landmark_5 = np.array(
        [
            face_landmark_106[38],
            face_landmark_106[88],
            face_landmark_106[86],
            face_landmark_106[52],
            face_landmark_106[61],
        ]
    )
    return face_landmark_5


def convert_face_landmark_203_to_5(face_landmark_203, use_mean_eyes=False):
    if use_mean_eyes:
        eye_left = np.mean(face_landmark_203[[0, 6, 12, 18]], axis=0)
        eye_right = np.mean(face_landmark_203[[24, 30, 36, 42]], axis=0)
    else:
        eye_left = face_landmark_203[197]
        eye_right = face_landmark_203[198]
    nose = face_landmark_203[201]
    lip_left = face_landmark_203[48]
    lip_right = face_landmark_203[66]
    face_landmark_5 = np.array([eye_left, eye_right, nose, lip_left, lip_right])
    return face_landmark_5


def convert_face_landmark_478_to_5(face_landmark_478, use_mean_eyes=False):
    if use_mean_eyes:
        eye_left = np.mean(face_landmark_478[[472, 471, 470, 469]], axis=0)
        eye_right = np.mean(face_landmark_478[[477, 476, 475, 474]], axis=0)
    else:
        eye_left = face_landmark_478[468]
        eye_right = face_landmark_478[473]
    nose = face_landmark_478[4]
    lip_left = face_landmark_478[61]
    lip_right = face_landmark_478[291]
    face_landmark_5 = np.array([eye_left, eye_right, nose, lip_left, lip_right])
    return face_landmark_5


def calc_face_yaw_pitch(kps):
    le = kps[0]
    re = kps[1]
    n = kps[2]
    lm = kps[3]
    rm = kps[4]
    dist_n_le = n[0] - le[0]
    dist_re_n = re[0] - n[0]
    diff = dist_n_le - dist_re_n
    sum_dist = dist_n_le + dist_re_n + 1e-06
    yaw = diff / sum_dist * 90.0
    eye_center_y = (le[1] + re[1]) / 2
    mouth_center_y = (lm[1] + rm[1]) / 2
    dist_eye_nose = n[1] - eye_center_y
    dist_nose_mouth = mouth_center_y - n[1]
    ratio = dist_eye_nose / (dist_nose_mouth + 1e-06)
    pitch = (1.0 - ratio) * 90.0
    return (yaw, pitch)
