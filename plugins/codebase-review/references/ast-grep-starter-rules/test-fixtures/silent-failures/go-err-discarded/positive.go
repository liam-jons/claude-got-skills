// Fixture for go-err-discarded — positive cases
package main

import "os"

func case1Open() {
	_, _ = os.Open("file.txt")
}

func case2Write(f *os.File, data []byte) {
	_, _ = f.Write(data)
}

func case3Exec() {
	_ = runCommand("ls")
}

func case4Multi() {
	_, _, _ = threeReturns()
}

func runCommand(cmd string) error {
	return nil
}

func threeReturns() (int, int, error) {
	return 0, 0, nil
}
