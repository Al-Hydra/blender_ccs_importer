from enum import Enum


class CCSTypes(Enum):
    Header = 0x0001
    IndexTable = 0x0002
    Setup = 0x0003
    Stream = 0x0005
    Object = 0x0100
    ObjectFrame = 0x0101
    ObjectController = 0x0102
    NoteFrame = 0x0108
    Material = 0x0200
    MaterialFrame = 0x0201
    MaterialController = 0x0202
    Texture = 0x0300
    Clut = 0x0400
    Camera = 0x0500 
    CameraFrame = 0x0502
    CameraController = 0x503
    Light = 0x0600
    AmbientFrame = 0x0601
    DistantLightFrame = 0x0602
    DistantLightController = 0x0603
    DirectLightFrame = 0x0604
    DirectLightController = 0x0605
    SpotLightFrame = 0x0606
    SpotLightController = 0x0607
    OmniLightFrame = 0x0608
    OmniLightController = 0x0609
    Animation = 0x0700
    Model = 0x0800
    ModelVertexFrame = 0x0802
    ModelNormalFrame = 0x0803
    Clump = 0x0900
    ExternalObject = 0x0a00
    HitModel = 0x0b00
    BoundingBox = 0x0c00
    Effect = 0x0e00
    Particle = 0x0d00
    ParticleAnmCtrl = 0x0d80
    ParticleGenerator = 0x0d90
    Blit_Group = 0x1000
    FrameBuffer_Page = 0x1100
    FrameBuffer_Rect = 0x1200
    DummyPosition = 0x1300
    DummyPositionRotation = 0x1400
    Layer = 0x1700
    Shadow = 0x1800
    ShadowFrame = 0x1801
    Morph = 0x1900
    MorphFrame = 0x1901
    MorphController = 0x1902
    StreamOutlineParam = 0x1a00
    OutlineFrame = 0x1a01
    StreamCelShadeParam = 0x1b00
    CelShadeFrame = 0x1b01
    StreamToneShadeParam = 0x1c00
    ToneShadeFrame = 0x1c01
    StreamFBSBlurParam = 0x1d00
    FBSBlurFrame = 0x1d01
    Sprite2Tbl = 0x1f00
    AnimationObject = 0x2000
    PCM_Audio = 0x2200
    PCMFrame = 0x2201
    Dynamics = 0x2300
    Binary_Blob = 0x2400
    SPD = 0x2700
    Frame = 0xff01

ccsDict = {
    0x0001: "",
    0x0002: "",
    0x0003: "",
    0x0005: "ccsStream",
    0x0100: "ccsObject",
    0x0101: "objectFrame",
    0x0102: "objectController",
    0x0108: "",
    0x0200: "ccsMaterial",
    0x0201: "",
    0x0202: "materialController",
    0x0300: "ccsTexture",
    0x0400: "ccsClut",
    0x0500: "ccsCamera",
    0x0502: "",
    0x0503: "cameraController",
    0x0600: "ccsLight",
    0x0601: "",
    0x0602: "",
    0x0603: "",
    0x0604: "",
    0x0605: "",
    0x0606: "",
    0x0607: "",
    0x0608: "",
    0x0609: "",
    0x0700: "ccsAnimation",
    0x0800: "ccsModel",
    0x0802: "",
    0x0803: "",
    0x0900: "ccsClump",
    0x0a00: "ccsExternalObject",
    0x0b00: "ccsHit",
    0x0c00: "ccsBox",
    0x0e00: "ccsEffect",
    0x0d00: "",
    0x0d80: "",
    0x0d90: "",
    0x1000: "",
    0x1100: "",
    0x1200: "",
    0x1300: "ccsDummyPos",
    0x1400: "ccsDummyPosRot",
    0x1700: "",
    0x1800: "",
    0x1801: "",
    0x1900: "ccsMorph",
    0x1901: "",
    0x1902: "morphController",
    0x1a00: "ccsStreamOutlineParam",
    0x1a01: "",
    0x1b00: "ccsStreamCelShadeParam",
    0x1b01: "",
    0x1c00: "ccsStreamToneShadeParam",
    0x1c01: "",
    0x1d00: "ccsStreamFBSBlurParam",
    0x1d01: "",
    0x1f00: "",
    0x2000: "ccsAnmObject",
    0x2200: "",
    0x2201: "",
    0x2300: "ccsDynamics",
    0x2400: "",
    0x2700: "",
    0xff01: "frame",
}