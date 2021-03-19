
# ![5G-CONTACT](https://5gcontact.av.it.pt/img/5g-contact-logo.png)

Here you'll find the public repository containing the computational applications developed under scope of the 5GCONTACT (https://5gcontact.av.it.pt) project.
The project ran from 2017 to 2021 and is now closed.

## SLIMANO - Slice Management and Orchestration Abstraction Framework

This framework provides an abstract mechanism for instantiating end-to-end network slices, composed by a chain of physical and virtual network functions. It supports plug-ins to interact with different network orchestration entities, namely different management and orchestration (MANO), Software Defined Networking (SDN) controllers and Radio Access Network (RAN) controllers. With this the framework is able to request network resources and coordinate the interaction among network orchestration entities for its instantiation and chaining in order to perform an end-to-end slice.

The SLIMANO project software is composed by three independent software applications:

* ### Slice Management and Orchestration Abstraction Framework Core

  It composes the engine and implemented plugins for enabling the instantiation of end-to-end network slices.

* ### Client

  It composes a client for instantiating network slices.

* ### Convergion Agents

  It composes a set of Conversion Agents that integrated different networks in network slicing management and orquestration environments.

## Expert System

The expert system is a network context framework realized through a simplified rule engine, where it is possible to upload a set of rules that dictate how the system should operate in certain conditions. It monitors several properties in real-time, that can either be raw values or classifications/predictions made by any Machine Learning/Deep Learning model. The system can be applied considering values coming from network entities (for network context), from connected devices (e.g., sensors and other terminals) and from services (i.e., feedback context from services such as indicating that video is being received in proper conditions), with the information being sent to the 5GCONTACT framework.

## Fireman

The fireman simulation emulates increments the Expert System to create a scenario where the fire brigade detects an urban fire and mobilizes to contain it. There are two main processes for this simulation. First is the fireman itself, which measures/simulates Co2 and the health condition of a fireman, whose information is sent to the 5GCONTACT framework. The framework keeps monitoring these values and intelligently decides when to act. In this simple scenario, there were only implemented two actions, moving the Expert System from the core network to the edge (and vice-versa) and rescuing a fireman when their vitals reach a critical point. The Expert System is a service that contains a set of rules and by analysing the real-time values from the fireman, decides on how to act.

## MAAS - Metal as a Service testbed

The MAAS, based on the Metal as a Service deployment, encompasses the necessary code scripts and configuration to deploy the infrastructure framework that allows SLIMANO to chain physical network elements and virtual network functions.

## Edge Mobility Manager

The Edge Mobility Manager emulates a handover between different Radio Access Network (RAN) endpoints, in a Multi-access Edge Computing (MEC) environment. It is composed of a SDN Controller Application that runs on top of the [ryu](https://ryu-sdn.org/) SDN Framework Controller, as well as the necessary running scripts for installing and configuring the necessary switch bridges in [Open vSwitch](https://www.openvswitch.org/). The SDN Controller Application exposes a REST interface that allows external entities to trigger the handover.

# Support or Contact

Having trouble with this page? Check out our project [website](http://5gcontact.av.it.pt)

