// Fixture for go-err-nil-empty — negative cases
package main

import (
	"fmt"
	"log"
	"os"
)

func case1LogReturn() error {
	_, err := os.Open("file.txt")
	if err != nil {
		log.Printf("open failed: %v", err)
		return err
	}
	return nil
}

func case2Wrap() error {
	_, err := os.Open("file.txt")
	if err != nil {
		return fmt.Errorf("opening file: %w", err)
	}
	return nil
}

func case3Panic() {
	_, err := os.Open("file.txt")
	if err != nil {
		panic(err)
	}
}

func case4NoIfErr() {
	// No if err != nil block at all
	_, _ = os.Open("file.txt")
}
