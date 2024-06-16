# -*- encoding: ascii -*-
"""
Project Settings
~~~~~~~~~~~~~~~~

"""


settings = dict(
    package="rjsmin",
    #
    # Wheels
    #
    wheels=dict(
        build="binary",
        specs={
            "aarch64": {
                "36": dict(manylinux="2014", musllinux="1_1"),
                "37": dict(manylinux="2014", musllinux="1_1"),
                "38": dict(manylinux="2014", musllinux="1_1"),
                "39": dict(manylinux="2014", musllinux="1_1"),
                "310": dict(manylinux="2014", musllinux="1_1"),
                "311": dict(manylinux="2014", musllinux="1_1"),
                "312": dict(manylinux="2014", musllinux="1_1"),
            },
            "x86_64": {
                "27": dict(manylinux="1"),
                "36": dict(manylinux="1", musllinux="1_1"),
                "37": dict(manylinux="1", musllinux="1_1"),
                "38": dict(manylinux="1", musllinux="1_1"),
                "39": dict(manylinux="1", musllinux="1_1"),
                "310": dict(manylinux="2010", musllinux="1_1"),
                "311": dict(manylinux="2014", musllinux="1_1"),
                "312": dict(manylinux="2014", musllinux="1_1"),
            },
            "i686": {
                "27": dict(manylinux="1"),
                "36": dict(manylinux="1", musllinux="1_1"),
                "37": dict(manylinux="1", musllinux="1_1"),
                "38": dict(manylinux="1", musllinux="1_1"),
                "39": dict(manylinux="1", musllinux="1_1"),
                "310": dict(manylinux="2010", musllinux="1_1"),
                "311": dict(manylinux="2014", musllinux="1_1"),
                "312": dict(manylinux="2014", musllinux="1_1"),
            },
        },
    ),
)
