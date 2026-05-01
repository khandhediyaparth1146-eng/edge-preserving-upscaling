all: libedge_bicubic.so

libedge_bicubic.so: edge_preserving_bicubic.cu
	nvcc -Xcompiler -fPIC -shared -o libedge_bicubic.so edge_preserving_bicubic.cu

clean:
	rm -f libedge_bicubic.so
