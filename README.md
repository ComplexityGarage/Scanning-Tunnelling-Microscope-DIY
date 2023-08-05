# Scanning Tunneling Microscope
# Authors 
- Paweł Chmolewski
# Description of the project 
Scanning tunneling microscope is a tool capable of imaging surfaces with atomic resolution in the air. The STM is based on concept of quantum tunneling effect.

This type of microscope works in two operating modes:
- Constant height mode
- Constant current mode
  
# Science and tech used 

| STM circuit overview |
| --- |
| ![STM circuit overview](STM_circuit_schematic.jpg) |

The amplifiers used in the circuit are powered from symmetric power supply which has the input EMI filter.

| STM Piezo Driver |
| --- |
| ![STM circuit overview](STM_piezo_driver.jpg) |

The Piezo driver is responsible for tip movement. It controls the movement of the piezo buzzer by generating signals Z+X, Z-X, Z+Y, Z-Y based on provided input signals X, Y, Z.

# State of the art


| STM Scan Head |
| --- |
| ![STM Scan Head](/IMG_0586.jpg) |
| The input of the preamplifier which is mounted on a STM scan head requires good insulation. It is only connected to the needle and the input node of the op amp is insulated by air wiring technique. During the data collection, the STM scan head is covered with metal to provide EMI shielding. |


| STM Vibration Isolation |
| --- |
| ![STM Vibration Isolation](/IMG_0594.jpg) |
| The good vibration isolation is essential for STM. Smallest mechanical oscillations affect on tip-sample distance and may cause that the tip crash into the sample. |

| Scanning Tunneling Microscope configuration |
| --- |
| ![Scanning Tunneling Microscope configuration](/IMG_0604.jpg) |

# What next?
The current version of microscope works in constant height mode. It could be developed by software modifications. Introducing a feedback loop which controls the voltage applied to the Z-axis electrode of the piezo scanner to maintain a constant tunneling current, allows it to operate in constant current mode. To protect STM scanning tip from accidental crashing into the sample, coarse approach might be motorized and controllled by the software. To provide better quality images, the noise could be reduced by building soundproof box.
# Sources
- [Dan Berard] (https://dberard.com)
- [Raspberry Pi] (https://www.raspberrypi.org/help/)
- [Analog Discovery] (https://digilent.com/reference/software/waveforms/waveforms-3/start)
- [Writing on GitHub] ( https://docs.github.com/en/get-started/writing-on-github ) 
