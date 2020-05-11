import multiprocessing as mp
import threading as th
from time import sleep


def writer(input, output):
    out = 0
    for _ in range(10):
        output.send(out)
        sleep(1)
        out ^= 1
    output.send('END')


def reader(input, output):
    printer = None
    cont = True

    while cont:
        printer = input.recv()
        if printer == 'END':
            cont = False
        print(printer)


if __name__ == "__main__":
    p_in, p_out = mp.Pipe()
    pr_writer = mp.Process(target=writer, args=(p_in, p_out))
    pr_reader = mp.Process(target=reader, args=(p_in, p_out))

    pr_writer.start()
    pr_reader.start()
    pr_writer.join()
    pr_reader.join()
    p_in.close()
    p_out.close()
