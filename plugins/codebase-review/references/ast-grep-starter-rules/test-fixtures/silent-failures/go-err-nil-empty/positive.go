// Fixture for go-err-nil-empty — positive cases
package main

import "os"

func case1() {
	_, err := os.Open("file.txt")
	if err != nil {
	}
}

func case2() {
	_, err := os.ReadFile("config.json")
	if err != nil {
	}
	// continues as if nothing happened
}

func case3(id string) {
	err := doThing(id)
	if err != nil {
	}
}

func doThing(id string) error {
	return nil
}
