import numpy as np
from colorspacious import cspace_convert, cspace_converter, deltaE

class DeficientColorSpace(object):
    """
    Template class for abstract colorspace transforms
    """
    def __init__(self, origin_space_name, cvd_type, severity=100,
                 dest_space_name='sRGB1'):
        self.severity = severity
        if cvd_type:
            cvd_spec = dict(name=origin_space_name,
                            cvd_type=cvd_type,
                            severity=severity)
            self.converter = cspace_converter(cvd_spec, dest_space_name)
        else:
            self.converter = cspace_converter(origin_space_name,
                                              dest_space_name)

    def _name_by_severity(self, name):
        """Properly name colorspace based on severity"""
        self.name = name
        if self.severity < 51:
            self.name += 'anomoly'
        else:
            self.name += 'opia'

    def _validate_input_image(self, putative_srgb):
        """Ensure input image is in an sRGB space"""
        max_value = int(putative_srgb.max())
        try:
            if max_value > 1:
                from_space = 'sRGB255'
            else:
                from_space = 'sRGB1'
            valid_srgb = cspace_convert(putative_srgb, from_space, 'sRGB1')
        except Exception as exception:
            raise exception
        return valid_srgb

    def convert(self, srgb_image):
        """
        Converts from defined colorspace to sRGB1
        """
        srgb_image = self._validate_input_image(srgb_image)
        return np.clip(self.converter(srgb_image), 0, 1)

class MonochromeColorSpace(DeficientColorSpace):
    """
    Unlike the single color deficient spaces, the monochrome colorspace
    requires a transformation into JCh (CIECAM02) colorspace where the
    chromaticity field is set to 0 (setting all hue variation to 0).  Then we
    can convert back from this color deficient space to sRGB1 as we do in the
    other deficient colorspaces.
    """
    def __init__(self, severity=100, dest_space_name='sRGB1'):
        super(MonochromeColorSpace, self).__init__('JCh', None, severity)
        self.dest_space_name = dest_space_name
        self.name = f'Monochrome ({severity}%)'

    def convert(self, srgb_image):
        """Slightly more complicated convert"""
        srgb_image = self._validate_input_image(srgb_image)
        grayscale = cspace_convert(srgb_image, 'sRGB1', 'JCh')

        if self.severity == 100:
            grayscale[..., 1] = 0
        else:
            grayscale[..., 1] *= self.severity/100

        converted = cspace_convert(grayscale, 'JCh', self.dest_space_name)
        return np.clip(converted, 0, 1)

class ProtanopiaColorSpace(DeficientColorSpace):
    """
    Protanopia colorspace converts from sRGB1+CVD to sRGB
    """
    def __init__(self, severity=100, dest_space_name='sRGB1'):
        super(ProtanopiaColorSpace, self).__init__('sRGB1+CVD',
                                                   'protanomaly',
                                                   severity,
                                                   dest_space_name)
        self._name_by_severity('Protan')

class DeuteranopiaColorSpace(DeficientColorSpace):
    """
    Deuteranopia colorspace converts from sRGB1+CVD to sRGB
    """
    def __init__(self, severity=100, dest_space_name='sRGB1'):
        super(DeuteranopiaColorSpace, self).__init__('sRGB1+CVD',
                                                     'deuteranomaly',
                                                     severity,
                                                     dest_space_name)
        self._name_by_severity('Deuteran')

class TritanopiaColorSpace(DeficientColorSpace):
    """
    Tritanopia colorspace converts from sRGB1+CVD to sRGB
    """
    def __init__(self, severity=100, dest_space_name='sRGB1'):
        super(TritanopiaColorSpace, self).__init__('sRGB1+CVD',
                                                   'tritanomaly',
                                                   severity,
                                                   dest_space_name)
        self._name_by_severity('Tritan')

class OriginalColorSpace(DeficientColorSpace):
    """
    Fake class for plotting the original in the same way as the others
    when using default options.
    """
    def __init__(self, severity=100, dest_color_name='sRGB255'):
        super(OriginalColorSpace, self).__init__('sRGB255', None, severity,
                                                 dest_color_name)
        self.name = 'Original'

    def convert(self, image):
        return image


def colordiff_3d(image, colorspace):
    """
    Compute the deltaE between an image and that image translated from a
    colorspace
    """
    return deltaE(image, colorspace.convert(image))

def colordiff_1d(image, colorspace, channel=0,
                 input_space='sRGB1', uniform_space='CAM02-UCS'):
    """
    Only compute distance along first axis of uniform space
    """
    uniform1 = cspace_convert(image, input_space, uniform_space)
    uniform2 = cspace_convert(colorspace.convert(image),
                              input_space, uniform_space)
    #return np.min(np.abs(uniform1 - uniform2), axis=-1)
    return np.abs(uniform1[..., channel] - uniform2[..., channel])

