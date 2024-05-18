/*
 * Copyright 2021 Free Software Foundation, Inc.
 *
 * This file is part of GNU Radio
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 */

/***********************************************************************************/
/* This file is automatically generated using bindtool and can be manually edited  */
/* The following lines can be configured to regenerate this file during cmake      */
/* If manual edits are made, the following tags should be modified accordingly.    */
/* BINDTOOL_GEN_AUTOMATIC(0)                                                       */
/* BINDTOOL_USE_PYGCCXML(0)                                                        */
/* BINDTOOL_HEADER_FILE(packet_pad2.h)                                        */
/* BINDTOOL_HEADER_FILE_HASH(b2e434a4d5f7a750e8183bd819862469)                     */
/***********************************************************************************/

#include <pybind11/complex.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

#include <foo/packet_pad2.h>
// pydoc.h is automatically generated in the build directory
#include <packet_pad2_pydoc.h>

void bind_packet_pad2(py::module& m)
{

    using packet_pad2    = ::gr::foo::packet_pad2;


    py::class_<packet_pad2, gr::tagged_stream_block, gr::block, gr::basic_block,
        std::shared_ptr<packet_pad2>>(m, "packet_pad2", D(packet_pad2))

        .def(py::init(&packet_pad2::make),
           py::arg("debug") = false,
           py::arg("delay") = false,
           py::arg("delay_sec") = 0.01,
           py::arg("pad_front") = 0,
           py::arg("pad_tail") = 0,
           D(packet_pad2,make)
        )
        



        ;




}








