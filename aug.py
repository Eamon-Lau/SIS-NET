from typing import List

import albumentations as albu
import matplotlib.pyplot as plt
import cv2
from PIL import Image
def get_transforms(size: int, scope: str = 'geometric', crop='random'):
    augs = {'strong': albu.Compose([albu.HorizontalFlip(),
                                    albu.ShiftScaleRotate(shift_limit=0.0, scale_limit=0.2, rotate_limit=20, p=.4),
                                    albu.ElasticTransform(),
                                    albu.OpticalDistortion(),
                                    albu.OneOf([
                                        albu.CLAHE(clip_limit=2),
                                        albu.IAASharpen(),
                                        albu.IAAEmboss(),
                                        albu.RandomBrightnessContrast(),
                                        albu.RandomGamma()
                                    ], p=0.5),
                                    albu.OneOf([
                                        albu.RGBShift(),
                                        albu.HueSaturationValue(),
                                    ], p=0.5),
                                    ]),
            'weak': albu.Compose([albu.HorizontalFlip(),
                                  ]),
            'geometric': albu.OneOf([albu.HorizontalFlip(always_apply=True),
                                     albu.ShiftScaleRotate(always_apply=True),
                                     albu.Transpose(always_apply=True),
                                     albu.OpticalDistortion(always_apply=True),
                                     albu.ElasticTransform(always_apply=True),
                                     ])
            }

    aug_fn = augs[scope]
    crop_fn = {'random': albu.RandomCrop(size, size, always_apply=True),
               'center': albu.CenterCrop(size, size, always_apply=True)}[crop]
    pad = albu.PadIfNeeded(size, size)

    pipeline = albu.Compose([aug_fn, crop_fn, pad], additional_targets={'target': 'image'})

    def process(a, b):
        # img = cv2.cvtColor(a, cv2.COLOR_BGR2RGB)
        # plt.figure()
        # plt.imshow(img)
        # plt.pause(0.001)
        #
        # img = cv2.cvtColor(b, cv2.COLOR_BGR2RGB)
        # plt.figure()
        # plt.imshow(img)
        # plt.pause(0.001)

        r = pipeline(image=a, target=b)
        return r['image'], r['target']

    return process


def get_normalize():
    normalize = albu.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])    # 归一化的目的简而言之，是使得没有可比性的数据变得具有可比性，同时又保持相比较的两个数据之间的相对关系，如大小关系
    normalize = albu.Compose([normalize], additional_targets={'target': 'image'})

    def process(a, b):
        r = normalize(image=a, target=b)
        return r['image'], r['target']

    return process


def _resolve_aug_fn(name):
    d = {
        'cutout': albu.Cutout,
        'rgb_shift': albu.RGBShift,
        'hsv_shift': albu.HueSaturationValue,
        'motion_blur': albu.MotionBlur,
        'median_blur': albu.MedianBlur,
        'snow': albu.RandomSnow,
        'shadow': albu.RandomShadow,
        'fog': albu.RandomFog,
        'brightness_contrast': albu.RandomBrightnessContrast,
        'gamma': albu.RandomGamma,
        'sun_flare': albu.RandomSunFlare,
        'sharpen': albu.IAASharpen,
        'jpeg': albu.JpegCompression,
        'gray': albu.ToGray,
        # ToDo: pixelize
        # ToDo: partial gray
    }
    return d[name]


def get_corrupt_function(config: List[dict]):
    augs = []
    for aug_params in config:
        name = aug_params.pop('name')
        cls = _resolve_aug_fn(name)
        prob = aug_params.pop('prob') if 'prob' in aug_params else .5
        augs.append(cls(p=prob, **aug_params))

    augs = albu.OneOf(augs)

    def process(x):
        return augs(image=x)['image']

    return process
