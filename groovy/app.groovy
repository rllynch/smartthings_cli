/**
*  SmartThings CLI Control
*
*  Copyright 2015 Richard L. Lynch <rich@richlynch.com>
*
*  Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
*  in compliance with the License. You may obtain a copy of the License at:
*
*      http://www.apache.org/licenses/LICENSE-2.0
*
*  Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
*  on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License
*  for the specific language governing permissions and limitations under the License.
*
*/

definition(
    name: "SmartThings CLI Control",
    namespace: "rllynch",
    author: "Richard L. Lynch",
    description: "CLI control of SmartThings devices",
    category: "My Apps",
    iconUrl: "https://s3.amazonaws.com/smartapp-icons/Convenience/Cat-Convenience.png",
    iconX2Url: "https://s3.amazonaws.com/smartapp-icons/Convenience/Cat-Convenience@2x.png",
    iconX3Url: "https://s3.amazonaws.com/smartapp-icons/Convenience/Cat-Convenience@2x.png",
    oauth: true)


preferences {
    section("Allow CLI Access to These Things...") {
        input "switches", "capability.switch", title: "Switch", required: false, multiple: true
        input "motions", "capability.motionSensor", title: "Motion", required: false, multiple: true
        input "temperatures", "capability.temperatureMeasurement", title: "Temperature", required: false, multiple: true
        input "humidities", "capability.relativeHumidityMeasurement", title: "Humidity", required: false, multiple: true
        input "contacts", "capability.contactSensor", title: "Contact", required: false, multiple: true
        input "accelerations", "capability.accelerationSensor", title: "Acceleration", required: false, multiple: true
        input "presences", "capability.presenceSensor", title: "Presence", required: false, multiple: true
        input "batteries", "capability.battery", title: "Battery", required: false, multiple: true
        input "threeaxes", "capability.threeAxis", title: "3 Axis", required: false, multiple: true
    }
}

mappings {
    path("/routine") {
        action: [
            GET: "listRoutines"
        ]
    }
    path("/:type") {
        action: [
            GET: "listDevices"
        ]
    }
    path("/:type/:id/:cmd") {
        action: [
            GET: "updateDevice"
        ]
    }
    path("/routine/:id") {
        action: [
            GET: "runRoutine"
        ]
    }
}

def installed() {
    log.debug "Installed with settings: ${settings}"

    initialize()
}

def updated() {
    log.debug "Updated with settings: ${settings}"

    unsubscribe()
    initialize()
}

def initialize() {
    // TODO: subscribe to attributes, devices, locations, etc.
}

private device_to_json(device, type) {
    if (!device) {
        return;
    }

    def values = [:]
    def json_dict = [id: device.id, label: device.label, type: type, value: values];

    def s = device.currentState(type)
    values['timestamp'] = s?.isoDate

    switch(type) {
        case "switch":
            values['state'] = (s?.value == "on")
            break
        case "motion":
            values['state'] = (s?.value == "active")
            break
        case "temperature":
            values['state'] = s?.value.toFloat()
            break
        case "humidity":
            values['state'] = s?.value.toFloat()
            break
        case "contact":
            values['state'] = (s?.value == "closed")
            break
        case "acceleration":
            values['state'] = (s?.value == "active")
            break
        case "presence":
            values['state'] = (s?.value == "present")
            break
        case "battery":
            values['state'] = s?.value.toFloat() / 100.0
            break
        case "threeAxis":
            values['x'] = s?.xyzValue?.x
            values['y'] = s?.xyzValue?.y
            values['z'] = s?.xyzValue?.z
            break
    }

    json_dict
}

def devices_for_type(type) {
    [
        switch:       switches,
        motion:       motions,
        temperature:  temperatures,
        humidity:     humidities,
        contact:      contacts,
        acceleration: accelerations,
        presence:     presences,
        battery:      batteries,
        threeAxis:    threeaxes
    ][type]
}

def listDevices() {
    devices_for_type(params.type).collect {
        device_to_json(it, params.type)
    }
}

void updateDevice() {
    def dev = devices_for_type(params.type).find { it.id == params.id }
    if (!dev) {
        httpError(404, "Device not found")
    } else {
        dev."$params.cmd"()
    }
}

def listRoutines() {
    location.getHelloHome().getPhrases().collect {
        [id: it.id, label: it.label]
    }
}

void runRoutine() {
    def home = location.getHelloHome()
    def routine = home.getPhrases().find { it.id == params.id }
    if (!routine) {
        httpError(404, "Routine not found")
    } else {
        home.execute(routine.label)
    }
}