// Fixture for go-err-discarded — negative cases
package main

import (
	"fmt"
	"os"
)

func case1Assigned() error {
	f, err := os.Open("file.txt")
	if err != nil {
		return err
	}
	defer f.Close()
	return nil
}

func case2BothAssigned() error {
	data, err := os.ReadFile("config.json")
	if err != nil {
		return err
	}
	fmt.Println(string(data))
	return nil
}

func case3FunctionResult() string {
	result := formatSomething("hello")
	return result
}

func formatSomething(s string) string {
	return s
}
