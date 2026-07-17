Projects CAN, FD, XL GUI samples presenting (almost) all features of PCAN-Basic API respectively for CAN Classic (CC), FD and XL communications.


Installation:
-------------
 * A JDK is required to build the samples
 * For each sample:
   * Folder 'NetBeans_Project' contains the configuration files to load the project with the IDE 'Apache NetBeans'
   * Scripts 'build' and 'run' (or Makefile on linux) are provided to respectively build and run the sample.
   * Windows: Library "PCAN-Basic_java.jar" is expected in the root of the sample.
   * Windows: Library "PCANBasic_JNI.dll" is expected in the root of the sample when using 'run' script.
   * Windows: For NetBeans users: library "PCANBasic_JNI.dll" is expected in the folder 'NetBeans_Project' when debugging/running the sample.


Usage:
------
To run the sample call:
 * on Windows:
  java --class-path "classes;PCAN-Basic_java.jar;" peak.can.Application
 * on Linux:
  java --class-path "classes:PCAN-Basic_java.jar:" peak.can.Application
   (or using the Makefile: make run)


Extra PCAN-Basic features:
--------------------------
Some features from PCAN-Basic API are not present in the GUI sample.
The following section adds short code samples for these.

 * LookUpChannel usage:
  // Create New instance of PCANBasic
    PCANBasic pcanBasic = new PCANBasic();
    // JNI Initialization
    pcanBasic.initializeAPI();
  // ...
  MutableTPCANHandle handle = new MutableTPCANHandle();
  TPCANStatus sts = pcanBasic.LookUpChannel(new StringBuffer("devicetype=pcan_usb"), handle);
  System.out.println("LookUpChannel: " + stsTmp + " => found handle is " + handle.getValue());